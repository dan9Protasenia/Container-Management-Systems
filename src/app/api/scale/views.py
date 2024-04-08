from fastapi import Body, Path

from src.app.api.container.service import ContainerService
from src.app.api.scale.service import ScaleService

container_service = ContainerService()
scale_service = ScaleService()


async def scale_container(container_id: str = Path(...), scale_target: int = Body(...)):
    result = scale_service.scale_container(container_id=container_id, scale_target=scale_target)
    return {"message": "Container scaled successfully", "result": result}


async def get_containers_count_by_image(image_name: str):
    containers_count = container_service.get_containers_count_by_image(image_name)
    return {"image_name": image_name, "containers_count": containers_count}


async def load_balance():
    target_container_id = scale_service.balance_load()
    if not target_container_id:
        return {"error": "Нет доступных контейнеров для балансировки"}

    return {"message": f"Запрос отправлен на контейнер {target_container_id}"}
