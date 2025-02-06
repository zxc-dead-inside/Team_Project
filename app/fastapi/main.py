from datetime import UTC, datetime

from api.v1 import films, genres, persons
from contextlib import asynccontextmanager

from core.config import settings
from db import elastic
from db import redis

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from api.api import api_router
from core.config import settings


@asynccontextmanager
async def  lifespan(api: FastAPI):
    redis.redis = Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT,
        db=settings.REDIS_CACHE_DB)
    elastic.es = AsyncElasticsearch(
        hosts=[
            f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
        ],
        basic_auth=(
            settings.ELASTICSEARCH_USERNAME,
            settings.ELASTICSEARCH_PASSWORD
        )
        if settings.ELASTICSEARCH_USERNAME
        else None
    )
    yield
    redis.redis.close()
    elastic.es.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/api/openapi",
    lifespan=lifespan

)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(films.router, prefix='/api/v1/films', tags=['films'])
app.include_router(genres.router, prefix='/api/v1/genres', tags=['genres'])
app.include_router(persons.router, prefix='/api/v1/persons', tags=['persons'])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(UTC)}
