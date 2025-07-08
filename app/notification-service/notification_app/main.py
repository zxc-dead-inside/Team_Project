from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kafka.producer import startup_kafka, shutdown_kafka
from api.admin import router as admin_router
from api.event import router as event_router
from core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan setup and teardown."""
    # Setup
    await startup_kafka()
    logger.info("Starting Notification Service")

    yield

    # Teardown
    await shutdown_kafka()
    logger.info("Shutting down Notification Service")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Notification Service API",
        description="API of an Admin panel and Notification service",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(event_router)

    return app


app = create_application()


@app.get("/")
def read_root():
    return {"message": "Notification Service API", "docs": "/docs"}
