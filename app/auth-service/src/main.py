"""Main application entry point for the Authentication Service."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.api.auth import public_router as auth_public_router
from src.api.auth import private_router as auth_private_router
from passlib.context import CryptContext
from src.api.health import router as health_router
from src.api.middleware.superuser_middleware import SuperuserMiddleware
from src.api.roles import router as roles_router
from src.api.user_roles import router as user_roles_router
from src.api.superuser import router as superuser_router
from src.api.users import router as users_router
from src.core.config import get_settings
from src.core.container import Container
from src.core.logger import setup_logging
from src.core.middleware.authentication import AuthenticationMiddleware
from src.tracing import setup_tracer

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
        redoc_url="/api/redoc" if settings.environment != "production" else None
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    # Routers without required authentication
    public_router = APIRouter()
    public_router.include_router(
        health_router, prefix="/api/health", tags=["Health"])
    public_router.include_router(auth_public_router)

    # Routers with required authentication
    private_router = APIRouter(
        dependencies=[Depends(AuthenticationMiddleware())])
    private_router.include_router(users_router)
    private_router.include_router(roles_router)
    private_router.include_router(user_roles_router)
    private_router.include_router(auth_private_router)
    private_router.include_router(superuser_router)

    # Include routers
    app.include_router(public_router)
    app.include_router(private_router)

    app.add_middleware(
        SuperuserMiddleware,
        audit_log_repository_getter=lambda app: app.container.audit_log_repository(),
    )

    # Tracing
    setup_tracer(app)

    return app


app = create_application()


@app.get("/")
async def root():
    """Root endpoint redirecting to documentation."""
    return {"message": "Welcome to the Authentication Service API", "docs": "/api/docs"}
