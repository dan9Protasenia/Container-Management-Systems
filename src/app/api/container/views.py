from src.app.api.container.service import ContainerService
from src.app.core.schemas.container import ContainerCreate

service = ContainerService()


def list_containers():
    return service.list_all_containers()


def get_container(container_id: str):
    return service.get_container_by_id(container_id)


def create_container(container_create: ContainerCreate):
    container = service.create_container(container_create)
    return container


def delete_container(container_id: str):
    service.delete_container(container_id)
    return {"ok": True}


def start_container(container_id: str):
    service.start_container(container_id)
    return {"ok": True}


def stop_container(container_id: str):
    service.stop_container(container_id)
    return {"ok": True}


def get_container_logs(container_id: str):
    return service.get_container_logs(container_id)
