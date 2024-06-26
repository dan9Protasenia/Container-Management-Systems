from fastapi import APIRouter, status

from .views import get_containers_count_by_image, scale_container

router = APIRouter()

router.add_api_route(
    path="/scale/{image_name}",
    endpoint=scale_container,
    methods=["POST"],
    status_code=status.HTTP_200_OK,
    summary="Scale a specific container",
)

router.add_api_route(
    path="/containers/count/{image_name}",
    endpoint=get_containers_count_by_image,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
    summary="Get the count of containers for a specific image",
    response_description="The number of containers created from the specified image",
)
