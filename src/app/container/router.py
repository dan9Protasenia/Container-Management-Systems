from fastapi import APIRouter
from starlette import status

from src.app.container.views import get_container, list_containers

router = APIRouter()

router.add_api_route(
    path="/containers",
    endpoint=list_containers,
    methods=["GET"],
    response_model="list_containers",
    status_code=status.HTTP_200_OK,
    description="Get a list of all containers",
)

router.add_api_route(
    path="/containers/{container_id}",
    endpoint=get_container,
    methods=["GET"],
    response_model="get_container",
    status_code=status.HTTP_200_OK,
    description="Retrieving a container by ID",
)
