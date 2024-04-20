import asyncio
import datetime
import itertools
import re
import threading
import time

import docker
from docker.errors import APIError, ImageNotFound, NotFound

from src.app.core.handlers.errors import DockerImageNotFoundError, DockerInternalError, NoLogsFoundError
from src.app.core.schemas.container import Container
from src.app.core.schemas.container import Container as ContainerSchema
from src.app.core.schemas.container import ContainerCreate, ContainerLog, LogEntry

client = docker.from_env()


class ContainerService:

    def __init__(self):
        self.containers = []
        self.initial_containers_count = len(self.containers)
        self.container_cycle = itertools.cycle(self.containers)
        self.update_containers_list()

    def update_containers_list(self):
        self.containers = self.list_active_containers()
        self.container_cycle = itertools.cycle(self.containers)

    @staticmethod
    def list_all_containers() -> list[ContainerSchema]:
        containers = client.containers.list(all=True)
        containers_data = []

        for container in containers:
            ports = container.attrs["NetworkSettings"]["Ports"]
            url = "http://localhost"
            labels = container.labels
            for port, port_data in ports.items():
                if port_data:
                    host_port = port_data[0]["HostPort"]
                    url = f"http://localhost:{host_port}"

            container_data = ContainerSchema(
                id=container.id,
                image=container.image.tags[0] if container.image.tags else "unknown",
                status=container.status,
                url=url,
                labels=labels,
            )
            containers_data.append(container_data)

        return containers_data

    @staticmethod
    async def create_container(container_data: ContainerCreate) -> Container:
        try:
            container_data.image = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: (
                    client.images.get(container_data.image)
                    if client.images.list(container_data.image)
                    else client.images.pull(container_data.image)
                ),
            )
            container = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: client.containers.create(
                    image=container_data.image.tags[0],
                    command=container_data.command,
                    labels=container_data.labels,
                    detach=True,
                    ports={"80/tcp": None},
                ),
            )
            container.start()
            await asyncio.sleep(1)
            container.reload()

            port = container.attrs["NetworkSettings"]["Ports"]["80/tcp"][0]["HostPort"]
            print(f"Образ {container_data.image.tags[0]} успешно!")

            return Container(
                id=container.id, image=container_data.image.tags[0], status="running", url=f"http://localhost:{port}"
            )
        except (ImageNotFound, NotFound) as e:
            print(f"Image {container_data.image} not found: {e}")

        except APIError as e:
            print(f"Failed to create container: {e}")

    @staticmethod
    def list_active_containers():
        docker_containers = client.containers.list(filters={"status": "running"})
        containers = []

        for docker_container in docker_containers:
            port_data = docker_container.attrs["NetworkSettings"]["Ports"].get("80/tcp")
            url = f"http://localhost:{port_data[0]['HostPort']}" if port_data else "http://localhost"
            labels = docker_container.labels

            containers.append(
                Container(
                    id=docker_container.id,
                    image=docker_container.image.tags[0] if docker_container.image.tags else "unknown",
                    status=docker_container.status,
                    url=url,
                    labels=labels,
                )
            )

        return containers

    @staticmethod
    def delete_container(container_id: str):
        try:
            container = client.containers.get(container_id)
            container.remove(force=True)

        except NotFound:
            raise DockerImageNotFoundError(f"Container {container_id} not found.")

        except APIError as e:
            raise DockerInternalError(f"Failed to delete container {container_id}: {e.explanation}")

    @staticmethod
    def start_container(container_id: str):
        try:
            container = client.containers.get(container_id)
            container.start()

        except NotFound:
            raise DockerImageNotFoundError(f"Container {container_id} not found.")

        except APIError as e:
            raise DockerInternalError(f"Failed to start container {container_id}: {e.explanation}")

    @staticmethod
    def stop_container(container_id: str):
        try:
            container = client.containers.get(container_id)
            container.stop()

        except NotFound:
            raise DockerImageNotFoundError(f"Container {container_id} not found.")

        except APIError as e:
            raise DockerInternalError(f"Failed to stop container {container_id}: {e.explanation}")

    @staticmethod
    def get_container_logs(container_id: str) -> ContainerLog:
        try:
            container = client.containers.get(container_id)
            raw_logs = container.logs().decode("utf-8")

            if not raw_logs:
                raise NoLogsFoundError(f"No logs found for container {container_id}.")

            log_entries = []
            for line in raw_logs.split("\n"):
                match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+Z) (.*)", line)

                if match:
                    timestamp, message = match.groups()
                    log_entries.append(LogEntry(timestamp=timestamp, message=message))

            return ContainerLog(logs=log_entries)

        except NotFound:
            raise DockerImageNotFoundError(f"Container {container_id} not found.")

        except APIError as e:
            raise DockerInternalError(f"Failed to get logs for container {container_id}: {e.explanation}")

    @staticmethod
    def get_containers_count() -> int:
        containers = client.containers.list(all=True)

        return len(containers)

    @staticmethod
    def get_containers_count_by_image(image_name: str):
        containers = client.containers.list(all=True)
        filtered_containers = [c for c in containers if c.attrs["Config"]["Image"] == image_name]

        return len(filtered_containers)

    @staticmethod
    def get_containers_by_image(image_name: str):
        containers = client.containers.list(all=True)

        return [c for c in containers if c.attrs["Config"]["Image"] == image_name]

    @staticmethod
    def restart_failed_containers():
        while True:
            containers = client.containers.list(all=True)
            for container in containers:
                try:
                    container.reload()
                    state = container.attrs["State"]
                    status = state["Status"]
                    exit_code = state.get("ExitCode", 0)
                    created_at = datetime.datetime.strptime(
                        container.attrs["Created"][:-4], "%Y-%m-%dT%H:%M:%S.%f"
                    ).replace(tzinfo=datetime.timezone.utc)

                    if (datetime.datetime.now(datetime.timezone.utc) - created_at).total_seconds() < 500:  # 5 минут
                        print(f"Контейнер {container.id} был недавно создан, пропускаем...")
                        continue

                    print(f"Контейнер {container.id} в состояни его код {exit_code}")
                    if status == "exited" and exit_code != 0:
                        print(f"Контейнер {container.id} завершился с ошибкой, перезапускаем...")
                        container.restart()
                        print(f"Контейнер {container.id} успешно перезапущен.")
                    else:
                        print(f"Контейнер {container.id} в состоянии {status}, пропускаем.")
                        print(f"код ошибки контейнера {exit_code}")
                except APIError as e:
                    print(f"Ошибка при обработке контейнера {container.id}: {e.explanation}")
                except Exception as e:
                    print(f"Неожиданная ошибка при обработке контейнера {container.id}: {str(e)}")
            time.sleep(60)


def start_health_check_loop():
    print("Стартовка цикла проверки состояния контей")
    health_check_thread = threading.Thread(target=ContainerService.restart_failed_containers, daemon=True)
    health_check_thread.start()


start_health_check_loop()
