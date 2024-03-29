from fastapi import APIRouter
from starlette import status

from src.app.api.container.views import (
    create_container,
    delete_container,
    get_container,
    get_container_logs,
    list_containers,
    start_container,
    stop_container,
)
from src.app.core.schemas.container import Container, ContainerLog

router = APIRouter()


router.add_api_route(
    path="/containers",
    endpoint=list_containers,
    methods=["GET"],
    response_model=list[Container],
    status_code=status.HTTP_200_OK,
    description="Get a list of all containers",
)

router.add_api_route(
    path="/containers/{container_id}",
    endpoint=get_container,
    methods=["GET"],
    response_model=Container,
    status_code=status.HTTP_200_OK,
    description="Retrieving a container by ID",
)

router.add_api_route(
    path="/containers",
    endpoint=create_container,
    methods=["POST"],
    response_model=Container,
    status_code=status.HTTP_201_CREATED,
    description="Create a new container",
)

router.add_api_route(
    path="/containers/{container_id}",
    endpoint=delete_container,
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a container",
)

router.add_api_route(
    path="/containers/{container_id}/start",
    endpoint=start_container,
    methods=["POST"],
    status_code=status.HTTP_200_OK,
    description="Start a container",
)

router.add_api_route(
    path="/containers/{container_id}/stop",
    endpoint=stop_container,
    methods=["POST"],
    status_code=status.HTTP_200_OK,
    description="Stop a container",
)

router.add_api_route(
    path="/containers/{container_id}/logs",
    endpoint=get_container_logs,
    methods=["GET"],
    response_model=ContainerLog,
    status_code=status.HTTP_200_OK,
    description="Get logs of a container",
)
