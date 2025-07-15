import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1.routers import api_router
from src.core.config import get_settings
from src.core.container import Container
from src.core.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    setup_logging()
    settings = get_settings()

    container = Container()
    Container.init_config_from_settings(container, settings)
    container.wire(modules=[__name__])
    app.container = container
    
    
    worker_task = asyncio.create_task(
        app.container.kafka_worker().start()
    )
    logging.info("Kafka worker task started")
    
    yield
    
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logging.info("Kafka worker task stopped")

def create_application() -> FastAPI:
    settings = get_settings()
    logging.info(f"Debug mode: {settings.debug_mode}")
    app = FastAPI(
        title=settings.app_title,
        description=settings.app_description,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.debug_mode else None,
        redoc_url="/api/redoc" if settings.debug_mode else None,
)
    app.include_router(api_router)
    return app

app = create_application()
