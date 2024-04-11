from fastapi import APIRouter, status

from src.app.api.balancer.views import proxy_request

router = APIRouter()

router.add_api_route(
    path="/proxy/{path:path}",
    endpoint=proxy_request,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
)
