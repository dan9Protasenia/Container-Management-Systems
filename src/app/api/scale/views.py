from src.app.api.container.service import ContainerService
from src.app.api.scale.service import ScaleService
from src.app.core.schemas.container import ContainerCreate

container_service = ContainerService()
scale_service = ScaleService()


async def scale_container(container_create: ContainerCreate):
    print(f"Масштабирование контейнера с образом {container_create.image}")
    container_create.labels = {"scale-purpose": "self-scaling"}
    await container_service.create_container(container_create)
    return {"message": "Container scaled successfully"}


async def get_containers_count_by_image(image_name: str):
    containers_count = container_service.get_containers_count_by_image(image_name)
    return {"image_name": image_name, "containers_count": containers_count}
