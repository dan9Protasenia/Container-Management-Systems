from fastapi import HTTPException

from src.app.container.services import ContainerService


def list_containers():
    containers = ContainerService.list_all_containers()
    return [container.short_id for container in containers]


def get_container(container_id: str):
    try:
        container = ContainerService.get_container_by_id(container_id)
        return {"id": container.short_id, "image": container.image.tags}

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
