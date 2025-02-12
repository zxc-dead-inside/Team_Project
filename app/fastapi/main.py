from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.api import api_router
from core.config import settings
from db.redis import redis_connector
from db import elastic
from db.elastic import es_connector

@asynccontextmanager
async def lifespan(api: FastAPI):
    await redis_connector.connect()
    await es_connector.connect()
    yield
    await redis_connector.disconnect()
    await es_connector.disconnect()

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
