"""Main application entry point for the Authentication Service."""

import logging
from contextlib import asynccontextmanager

from passlib.context import CryptContext
from src.api.auth import router as auth_router
from src.api.health import router as health_router
from src.api.roles import router as roles_router
from src.api.user_roles import router as user_roles_router
from src.api.users import router as users_router
from src.core.config import get_settings
from src.core.container import Container
from src.core.logger import setup_logging
from src.db.models.user import User
from src.api.middleware.anonymous_user_middleware import AnonymousUserMiddleware

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan setup and teardown."""
    # Setup
    settings = get_settings()
    setup_logging(settings.log_level)
    container = Container()

    Container.init_config_from_settings(container, settings)
    app.container = container

    user_service = container.user_service()
    anonymous_user = await user_service.get_by_username("anonymous")

    if not anonymous_user:
        logging.warning("Anonymous user not found in database. Creating.")
        anonymous_user = User(
            username="anonymous",
            email="anonymous@example.com",
            password=pwd_context.hash("anonymous"),
            is_active=False,
            is_superuser=False,
        )
        anonymous_user = await user_service.create_user(anonymous_user)

    app.state.anonymous_user = anonymous_user

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

    app.add_middleware(AnonymousUserMiddleware)

    # Include routers
    app.include_router(health_router, prefix="/api/health", tags=["Health"])
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(roles_router)
    app.include_router(user_roles_router)

    return app


app = create_application()


@app.get("/")
async def root():
    """Root endpoint redirecting to documentation."""
    return {"message": "Welcome to the Authentication Service API", "docs": "/api/docs"}
