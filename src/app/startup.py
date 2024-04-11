from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.app.api.init import init_routers


def create_app() -> FastAPI:
    app = FastAPI(
        docs_url="/documentation",
        openapi_url="/openapi.json",
        title="Container Management Systems",
        description="description",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_routers(app)

    app.mount("/static", StaticFiles(directory="src/app/static"), name="static")

    return app
