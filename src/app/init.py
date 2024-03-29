from fastapi import FastAPI

from src.app.api import container, metrics, scale


def init_routers(app: FastAPI) -> None:
    app.include_router(container, prefix="", tags=["container"])
    app.include_router(metrics, prefix="", tags=["metrics"])
    app.include_router(scale, prefix="", tags=["scale"])
