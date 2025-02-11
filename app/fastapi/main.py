from contextlib import asynccontextmanager
from datetime import UTC, datetime

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from api.api import api_router
from core.config import settings
from db import elastic
from db import redis
from db.elastic import es_connector


@asynccontextmanager
async def  lifespan(api: FastAPI):
    redis.redis = Redis(
        host=settings.redis_host, port=settings.redis_port,
        db=settings.redis_cache_db)
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
    await es_connector.connect()
    yield
    redis.redis.close()
    elastic.es.close()
    es_connector.disconnect()

app = FastAPI(
    title=settings.project_name,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url="/api/openapi",
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
