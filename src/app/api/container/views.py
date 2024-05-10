import docker

from src.app.api.container.service import ContainerService, ContainerInfoService
from src.app.core.schemas.container import ContainerCreate

client = docker.from_env()
container_service = ContainerService(client)
container_info_service = ContainerInfoService(client)


def list_containers():
    return container_info_service.list_all_containers()


async def create_container(container_create: ContainerCreate):
    container = await container_service.create_container(container_create)
    return container


def delete_container(container_id: str):
    container_service.delete_container(container_id)
    return {"ok": True}


def start_container(container_id: str):
    container_service.start_container(container_id)
    return {"ok": True}


def stop_container(container_id: str):
    container_service.stop_container(container_id)
    return {"ok": True}


def get_container_logs(container_id: str):
    return container_info_service.get_container_logs(container_id)
