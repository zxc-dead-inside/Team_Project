"""Main application entry point for the Authentication Service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.api.auth import auth_router
from src.core.config import get_settings
from src.core.container import Container
from src.core.logger import setup_logging
from src.db.database import get_database
from src.db.redis import get_redis



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan setup and teardown."""
    # Setup
    settings = get_settings()
    setup_logging(settings.log_level)
    container = Container()

    Container.init_config_from_settings(container, settings)
    app.container = container

    # Start services
    logging.info(f"Starting {settings.project_name} in {settings.environment} mode")
    db_connector = get_database(str(settings.database_url))
    redis_connector = get_redis(str(settings.redis_url)).connect()
    yield
    await db_connector.dispose()
    redis_connector.close()

    # Teardown
    logging.info(f"Shutting down {settings.project_name}")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Authentication Service",
        description="API for user authentication and authorization",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.environment != "production" else None,
        redoc_url="/api/redoc" if settings.environment != "production" else None,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_router)
    app.include_router(auth_router)
    return app


app = create_application()


@app.get("/")
async def root():
    """Root endpoint redirecting to documentation."""
    return {"message": "Welcome to the Authentication Service API", "docs": "/api/docs"}
