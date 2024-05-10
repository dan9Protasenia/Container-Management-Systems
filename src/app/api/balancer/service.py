import asyncio
import json
from threading import Thread

import httpx

from src.app.api.container.service import ContainerService, ContainerInfoService
from src.app.api.metrics.service import MetricsService
from src.app.api.metrics.views import get_container_metrics
from src.app.api.scale.service import ScaleService
from src.app.core.schemas.container import ContainerCreate


class LoadBalancer:
    def __init__(self, client):
        self.client = client
        self.scale_service = ScaleService(client)
        self.metrics_service = MetricsService(client)
        self.container_service = ContainerService(client)
        self.container_info_service = ContainerInfoService(client)

    def start(self):
        thread = Thread(target=self.handle_docker_events, daemon=True)
        thread.start()
        asyncio.create_task(self.check_and_scale())

    async def handle_docker_events(self):
        for event in self.client.events(decode=True):
            if event.get("Type") == "container":
                print(f"Обработка события: {event}")
                self.container_service.update_containers_list()

    async def get_least_loaded_container(self):
        least_loaded = None
        lowest_cpu_usage = "inf"

        for container in self.container_service.containers:
            metrics = await get_container_metrics(container.id)
            cpu_usage = metrics["cpu_usage"].rstrip("%")

            if cpu_usage < lowest_cpu_usage or (cpu_usage == lowest_cpu_usage):
                least_loaded = container
                lowest_cpu_usage = cpu_usage

        return least_loaded

    async def proxy_request(self, path: str):
        container = await self.get_least_loaded_container()

        if not container:
            return {"error": "Нет доступных контейнеров"}

        url = f"{container.url}/{path}"
        print(f"Перенаправление на контейнер: {container.id} с URL {url}")

        try:
            async with httpx.AsyncClient() as clients:
                response = await clients.get(url)

            if response.headers.get("Content-Type", "").startswith("application/json"):
                return {"container_id": container.id, "data": response.json()}
            else:
                return {"container_id": container.id, "data": response.text}

        except httpx.HTTPError as e:
            print(f"Ошибка при запросе к контейнеру: {e}")

            return {"error": "Ошибка при запросе к контейнеру"}

    async def check_and_scale(self):
        print("Checking and scaling")
        while True:
            average_cpu_load = await self.get_average_cpu_load()
            print(f"Средняя загрузка процессора: {average_cpu_load}")

            if average_cpu_load > 57:
                create_data = ContainerCreate(
                    image="app:latest", command="", labels={"scale-purpose": "scale-up"}, env={}
                )
                await self.scale_service.scale_up(create_data)

            elif average_cpu_load < 30:
                await self.scale_service.scale_down()

            await asyncio.sleep(10)

    async def get_average_cpu_load(self):
        total_cpu_load = 0
        active_containers = [container.id for container in self.container_info_service.list_active_containers()]

        if not active_containers:
            return 0

        valid_counts = 0

        for container in active_containers:
            cpu_load = await self.get_cpu_load(container)
            if cpu_load is not None:
                total_cpu_load += cpu_load
                valid_counts += 1

        if valid_counts == 0:
            return 0

        average_cpu_load = total_cpu_load / valid_counts

        return average_cpu_load

    async def get_cpu_load(self, container_id):
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            if not stats:
                return None

            cpu_delta = (
                    stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )

            system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]

            if system_cpu_delta == 0:
                print(f"Данные о загрузке CPU для контейнера {container_id} не доступны для анализа.")
                return None

            number_cpus = stats["cpu_stats"]["online_cpus"]

            cpu_usage_percentage = (cpu_delta / system_cpu_delta) * number_cpus * 100.0

            return cpu_usage_percentage

        except json.decoder.JSONDecodeError:
            print(f"Ошибка при декодировании ответа от API для контейнера {container_id}.")
            return None
        except KeyError as e:
            print(f"Отсутствует ожидаемое поле в ответе от API для контейнера {container_id}: {e}")
            return None
        except Exception as e:
            print(f"Неизвестная ошибка при получении статистики для контейнера {container_id}: {str(e)}")
            return None
