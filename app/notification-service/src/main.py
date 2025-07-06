import logging
from contextlib import asynccontextmanager

from src.api import router

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan setup and teardown."""
    # Setup
    logging.info("Starting Notification Service")

    yield

    # Teardown
    logging.info("Shutting down Notification Service")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Notification Service API",
        description="Административная панель для создания рассылок",
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

    app.include_router(router, prefix="/api/v1")

    return app


app = create_application()


@app.get("/")
def read_root():
    return {"message": "Notification Service API", "docs": "/docs"}
