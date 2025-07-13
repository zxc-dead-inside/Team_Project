from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.api import api_router
from core.config import settings
from db.elastic import es_connector
from db.redis import redis_connector

from core.logging_setup import setup_logging
from core.sentry_config import (
    setup_sentry, SentryContextMiddleware, SentryStructuredLogger
)
from middleware.logging import logging_middleware


setup_sentry()

setup_logging()
app_logger = SentryStructuredLogger(__name__)



@asynccontextmanager
async def lifespan(api: FastAPI):
    app_logger.info("Starting FastAPI application", service="fastapi")
    try:
        await redis_connector.connect()
        app_logger.info("Redis connected successfully")

        await es_connector.connect()
        app_logger.info("Elasticsearch connected successfully")

        yield

    except Exception as e:
        app_logger.error("Error during startup", error=e)
        raise
    finally:
        app_logger.info("Shutting down FastAPI application")
        await redis_connector.disconnect()
        await es_connector.disconnect()



app = FastAPI(
    title=settings.project_name,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    description="API documentation",
    docs_url="/docs",
    redoc_url="/redoc",
    version="1.0.0",
    lifespan=lifespan,
)

# Add Sentry context middleware before other middleware
app.add_middleware(SentryContextMiddleware)

# Logging middleware
app.middleware("http")(logging_middleware)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_str)
