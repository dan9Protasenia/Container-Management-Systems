import asyncio
import datetime
import json

import httpx
from threading import Thread
from src.app.api.container.service import ContainerService
from src.app.api.metrics.service import MetricsService
from src.app.api.metrics.views import get_container_metrics
from src.app.core.schemas.container import Container
import docker

from docker.errors import APIError, ImageNotFound, NotFound

client = docker.from_env()
metrics_service = MetricsService()
container_service = ContainerService()

import itertools

DEFAULT_CONTAINER_CONFIG = {
    "image": "app1:latest",
}


class LoadBalancer:
    def __init__(self):
        self.containers = []
        self.container_cycle = itertools.cycle(self.containers)
        self.update_containers_list()
        self.initial_containers_count = len(self.containers)

        thread = Thread(target=self.handle_docker_events, daemon=True)
        thread.start()

        asyncio.create_task(self.check_and_scale())

    @staticmethod
    async def create_container(image: str, command: str = None, labels: dict = None):
        try:
            image = await asyncio.get_running_loop().run_in_executor(None, lambda: client.images.get(image) if client.images.list(image) else client.images.pull(image))
            container = await asyncio.get_running_loop().run_in_executor(None, lambda: client.containers.create(
                image=image.tags[0],
                command=command,
                labels=labels,
                detach=True,
                ports={'80/tcp': None}
            ))
            container.start()
            await asyncio.sleep(1)
            container.reload()

            port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
            print(f"Образ {image.tags[0]} успешно заг")

            return Container(id=container.id, image=image.tags[0], status="running", url=f"http://localhost:{port}")
        except (ImageNotFound, NotFound) as e:
            print(f"Image {image} not found: {e}")

        except APIError as e:
            print(f"Failed to create container: {e}")

    def update_containers_list(self):
        self.containers = self.list_active_containers()
        self.container_cycle = itertools.cycle(self.containers)

    def update_containers(self, containers):
        self.container_cycle = itertools.cycle(containers)

    def get_next_container(self):
        if not self.containers:

            return None
        return next(self.container_cycle)

    async def handle_docker_events(self):
        for event in client.events(decode=True):
            if event.get("Type") == "container":
                print(f"Обработка события: {event}")
                self.update_containers_list()

    async def get_least_loaded_container(self):
        least_loaded = None
        lowest_cpu_usage = float('inf')

        for container in self.containers:
            metrics = await get_container_metrics(container.id)
            cpu_usage = float(metrics["cpu_usage"].rstrip('%'))

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
            async with httpx.AsyncClient() as client:
                response = await client.get(url)

            if response.headers.get('Content-Type', '').startswith('application/json'):
                return {"container_id": container.id, "data": response.json()}
            else:
                return {"container_id": container.id, "data": response.text}

        except httpx.HTTPError as e:
            print(f"Ошибка при запросе к контейнеру: {e}")

            return {"error": "Ошибка при запросе к контейнеру"}

    async def check_and_scale(self):
        while True:
            average_cpu_load = await self.get_average_cpu_load()
            print(f"Средняя загрузка процессора: {average_cpu_load}")

            if average_cpu_load > 57:
                await self.scale_up()

            elif average_cpu_load < 30:
                await self.scale_down()

            await asyncio.sleep(10)

    async def scale_up(self):
        print(f"Масштабирование вверх")
        config = DEFAULT_CONTAINER_CONFIG
        labels = {"scale-purpose": "scale-up"}
        await self.create_container(image=config['image'], command=config.get('command'), labels=labels)

    async def scale_down(self):
        current_containers = self.list_active_containers()

        if len(current_containers) <= self.initial_containers_count:
            return

        containers_to_remove = []

        for container in current_containers:
            docker_container = client.containers.get(container.id)
            created_at_str = docker_container.attrs['Created']
            created_at = datetime.datetime.strptime(created_at_str[:-4], "%Y-%m-%dT%H:%M:%S.%f").replace(
                tzinfo=datetime.timezone.utc)
            print(f"Контейнер {docker_container.short_id}: время создания {created_at}")

            container_label_value = docker_container.attrs['Config']['Labels'].get('scale-purpose', None)

            if container_label_value == "scale-up":
                print(f"Контейнер {docker_container.short_id} помечен для удаления.")
                containers_to_remove.append(docker_container)

            else:
                print(f"Контейнер {docker_container.short_id} не подходит для удаления.")

        for docker_container in containers_to_remove:
            try:
                await asyncio.get_running_loop().run_in_executor(None, lambda: docker_container.remove(force=True))
                print(f"Контейнер {docker_container.short_id} успешно удален.")
            except APIError as e:
                print(f"Ошибка при удалении контейнера {docker_container.short_id}: {e}")

        self.update_containers_list()

    async def get_average_cpu_load(self):
        total_cpu_load = 0
        active_containers = [container.id for container in self.list_active_containers()]
        print(f'стадия - 1')

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

    @staticmethod
    async def get_cpu_load(container_id):
        try:
            container = client.containers.get(container_id)
            stats = container.stats(stream=False)

            if not stats:
                return None

            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                        stats["precpu_stats"]["cpu_usage"]["total_usage"]

            system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                               stats["precpu_stats"]["system_cpu_usage"]

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

    @staticmethod
    def list_active_containers():
        docker_containers = client.containers.list(filters={"status": "running"})
        containers = []

        for docker_container in docker_containers:
            port_data = docker_container.attrs['NetworkSettings']['Ports'].get('80/tcp')
            url = f"http://localhost:{port_data[0]['HostPort']}" if port_data else "http://localhost"
            labels = docker_container.labels

            containers.append(Container(
                id=docker_container.id,
                image=docker_container.image.tags[0] if docker_container.image.tags else "unknown",
                status=docker_container.status,
                url=url,
                labels=labels
            ))

        return containers


load_balancer = LoadBalancer()


class ScaleService:

    def scale_container(self, container_id: str, scale_target: int):
        container = client.containers.get(container_id)
        image_name = container.attrs["Config"]["Image"]
        current_containers = container_service.get_containers_by_image(image_name)
        current_count = len(current_containers)

        if current_count < scale_target:
            self.start_new_containers(image_name, scale_target - current_count)

        elif current_count > scale_target:
            self.stop_excess_containers(current_containers, current_count - scale_target)

        return {"container_id": container_id, "scaled_to": scale_target}

    @staticmethod
    def start_new_containers(image_name: str, count: int):
        for _ in range(count):
            client.containers.run(image_name, detach=True)

    @staticmethod
    def stop_excess_containers(containers: list, count: int):
        for container in containers[:count]:
            container.stop()
            container.remove()

    def scale(self, container_id: str, scale_target: int):
        container = client.containers.get(container_id)
        image_name = container.attrs["Config"]["Image"]

        current_containers = container_service.get_containers_by_image(image_name)
        current_count = len(current_containers)

        if current_count < scale_target:
            self.start_new_containers(image_name, scale_target - current_count)

        elif current_count > scale_target:
            self.stop_excess_containers(current_containers, current_count - scale_target)

        updated_containers = container_service.get_containers_by_image(image_name)
        load_balancer.update_containers(updated_containers)

        return {"container_id": container_id, "scaled_to": scale_target}
