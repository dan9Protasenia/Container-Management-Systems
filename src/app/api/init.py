from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from src.app.api import balancer, container, metrics, scale
from src.app.core.handlers.errors import BaseError, DockerImageNotFoundError, DockerInternalError, NoLogsFoundError
from src.app.core.handlers.handlers import (
    base_error_handler,
    docker_image_not_found_error_handler,
    docker_internal_error_handler,
    generic_exception_handler,
    http_exception_handler,
    no_logs_found_exception_handler,
    validation_exception_handler,
)


def init_routers(app: FastAPI) -> None:
    app.include_router(container, prefix="", tags=["container"])
    app.include_router(metrics, prefix="", tags=["metrics"])
    app.include_router(scale, prefix="", tags=["scale"])
    app.include_router(balancer, prefix="", tags=["balancer"])

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(BaseError, base_error_handler)
    app.add_exception_handler(DockerImageNotFoundError, docker_image_not_found_error_handler)
    app.add_exception_handler(DockerInternalError, docker_internal_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(NoLogsFoundError, no_logs_found_exception_handler)
