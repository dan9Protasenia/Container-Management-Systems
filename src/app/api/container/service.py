import re

import docker
from docker.errors import APIError, ImageNotFound, NotFound

from src.app.core.handlers.errors import DockerImageNotFoundError, DockerInternalError, NoLogsFoundError
from src.app.core.schemas.container import Container as ContainerSchema
from src.app.core.schemas.container import ContainerCreate, ContainerLog, LogEntry

client = docker.from_env()


class ContainerService:
    @staticmethod
    def list_all_containers() -> list[ContainerSchema]:
        containers = client.containers.list(all=True)
        containers_data = []

        for container in containers:
            ports = container.attrs['NetworkSettings']['Ports']
            port_data = ports.get('80/tcp')

            if port_data:
                print(f' infa pro port_data{port_data}')
                host_port = port_data[0]['HostPort']
                url = f"http://localhost:{host_port}"

            else:
                print("Порт 80/tcp недоступен для этого контейнера.")
                url = "http://localhost"

            container_data = ContainerSchema(
                id=container.id,
                image=container.image.tags[0] if container.image.tags else "unknown",
                status=container.status,
                url=url
            )
            containers_data.append(container_data)

        return containers_data

    @staticmethod
    def get_container_by_id(container_id: str) -> ContainerSchema:
        try:
            container = client.containers.get(container_id)

            return ContainerSchema(id=container.id, image=container.attrs["Config"]["Image"], status=container.status)

        except NotFound:
            raise DockerImageNotFoundError(f"Container {container_id} not found.")

        except APIError as e:
            raise DockerInternalError(f"Failed to get container {container_id}: {e.explanation}")

    @staticmethod
    def create_container(container_data: ContainerCreate) -> ContainerSchema:
        try:
            image = client.images.get(container_data.image)
            print(f"Образ {container_data.image} найден локально.")
        except NotFound:
            try:
                image = client.images.pull(container_data.image)
                print(f"Образ {container_data.image} успешно загружен из Docker Hub.")

            except ImageNotFound:
                raise DockerImageNotFoundError(f"Image {container_data.image} not found.")

            except APIError as e:
                raise DockerInternalError(f"Failed to pull image {container_data.image}: {e.explanation}")

        try:
            container = client.containers.create(
                image=container_data.image,
                command=container_data.command,
                detach=True,
                ports={'80/tcp': None}
            )
            container.start()
            container.reload()
            port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
            return ContainerSchema(id=container.id, image=container.attrs["Config"]["Image"], status=container.status,
                                   url=f"http://localhost:{port}")
        except APIError as e:
            raise DockerInternalError(f"Failed to create container: {e.explanation}")

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
