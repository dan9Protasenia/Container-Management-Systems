from fastapi import FastAPI

from src.app.api.init import init_routers


def create_app() -> FastAPI:
    app = FastAPI(
        docs_url="/documentation",
        openapi_url="/openapi.json",
        title="Container Management Systems",
        description="description",
        version="1.0.0",
    )
    init_routers(app)
    return app
