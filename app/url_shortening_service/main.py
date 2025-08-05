from contextlib import asynccontextmanager

from api.dependencies import container
from api.health import health_router
from api.redirect import redirect_router
from api.v1 import api_router
from core.logging import configure_logging, get_logger
from core.settings import settings
from models import Base

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting URL Shortening Service", version=settings.app_version)

    container.wire(modules=["api.dependencies"])

    async_engine = container.async_db_engine()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await async_engine.dispose()
    
    logger.info("Shutting down URL Shortening Service")


app = FastAPI(
    title=settings.app_name,
    description="Microservice for shortening URLs for notification system",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(redirect_router)
app.include_router(api_router, prefix="/api/v1")