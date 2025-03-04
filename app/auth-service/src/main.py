"""Main application entry point for the Authentication Service."""

import logging
from contextlib import asynccontextmanager

from src.api.auth import router as auth_router
from src.api.health import router as health_router
from src.core.config import get_settings
from src.core.container import Container
from src.core.logger import setup_logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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

    yield

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
    app.include_router(health_router, prefix="/api/health", tags=["Health"])
    app.include_router(auth_router)

    return app


app = create_application()


@app.get("/")
async def root():
    """Root endpoint redirecting to documentation."""
    return {"message": "Welcome to the Authentication Service API", "docs": "/api/docs"}