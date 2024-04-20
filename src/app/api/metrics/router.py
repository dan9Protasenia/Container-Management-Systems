from typing import Any, Dict

from fastapi import APIRouter, Path
from starlette import status

from src.app.api.metrics.views import get_container_metrics

router = APIRouter()

router.add_api_route(
    path="/containers/{container_id}/metrics",
    endpoint=get_container_metrics,
    methods=["GET"],
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get detailed metrics for a specific container",
)
