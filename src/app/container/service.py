import docker
from docker.models.containers import Container

client = docker.from_env()


class ContainerService:
    @staticmethod
    def list_all_containers() -> list:
        containers = client.containers.list(all=True)

        return containers

    @staticmethod
    def get_container_by_id(container_id: str) -> Container:
        container = client.containers.get(container_id)

        return container
