from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .errors import BaseError, DockerImageNotFoundError, DockerInternalError, NoLogsFoundError


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"message": "Validation Error", "details": exc.errors()},
    )


async def base_error_handler(request: Request, exc: BaseError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )


async def docker_image_not_found_error_handler(request: Request, exc: DockerImageNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )


async def docker_internal_error_handler(request: Request, exc: DockerInternalError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )


async def no_logs_found_exception_handler(request: Request, exc: NoLogsFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )
