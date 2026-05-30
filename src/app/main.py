from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import install_handlers
from app.api.v1.router import router as v1_router
from app.config import get_settings
from app.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(get_settings().log_level)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AFM LbL Backend", lifespan=lifespan)
    install_handlers(app)
    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()
