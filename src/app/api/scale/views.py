from fastapi import Body, Path

from src.app.api.container.service import ContainerService
from src.app.api.scale.service import ScaleService, LoadBalancer
from src.app.core.schemas.container import ScaleRequest

container_service = ContainerService()
scale_service = ScaleService()
load_service = LoadBalancer()


async def scale_container(container_id: str = Path(...), scale_target: int = Body(...)):
    result = scale_service.scale_container(container_id=container_id, scale_target=scale_target)
    return {"message": "Container scaled successfully", "result": result}


async def get_containers_count_by_image(image_name: str):
    containers_count = container_service.get_containers_count_by_image(image_name)
    return {"image_name": image_name, "containers_count": containers_count}


async def scale(request: ScaleRequest):
    target_container_id = scale_service.scale(request.container_id, request.scale_target)

    return {"message": f"Запрос отправлен на контейнер {target_container_id}"}


async def proxy_request(path: str):
    return await load_service.proxy_request(path)
