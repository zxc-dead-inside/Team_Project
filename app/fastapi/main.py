from contextlib import asynccontextmanager
from datetime import UTC, datetime

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.api import api_router
from core.config import settings
from db.redis import redis_connector
from db import elastic


@asynccontextmanager
async def lifespan(api: FastAPI):
    await redis_connector.connect()
    elastic.es = AsyncElasticsearch(
        hosts=[
            f"http://{settings.elasticsearch_host}:{settings.elasticsearch_port}"
        ],
        basic_auth=(
            settings.elasticsearch_username,
            settings.elasticsearch_password
        )
        if settings.elasticsearch_username
        else None
    )
    yield
    await redis_connector.disconnect()
    elastic.es.close()

app = FastAPI(
    title=settings.project_name,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    description="API documentation",
    docs_url="/docs",
    redoc_url="/redoc",
    version="1.0.0",
    lifespan=lifespan
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(UTC)}
