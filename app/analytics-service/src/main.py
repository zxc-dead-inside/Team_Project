"""Main application entry point for the Analytics Service."""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from src.api import health_router, metrics_router
from src.core import get_settings, setup_logging, Container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan setup and teardown."""
    # Setup
    settings = get_settings()
    container = Container()
    Container.init_config_from_settings(container, settings)
    await container.kafka_producer().start()
    container.wire(modules=['src.api.v1.metrics', 'src.api.health'])
    app.container = container

    # Start services
    logging.info(
        f"Starting {settings.project_name} in {settings.environment} mode")

    yield

    # Teardown
    logging.info(f"Shutting down {settings.project_name}")

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        description=f"API for {settings.project_name}",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.environment != "production" else None,
        redoc_url="/api/redoc" if settings.environment != "production" else None
    )

    # Init router
    app.include_router(health_router, prefix="/api/health", tags=["Health"])
    app.include_router(metrics_router, prefix="/api/v1", tags=["Metrics"])

    return app


app = create_application()


@app.get("/")
async def root():
    """Root endpoint redirecting to documentation."""
    return {
        "message": "Welcome to the Analytics Service API",
        "docs": "/api/docs"
    }
