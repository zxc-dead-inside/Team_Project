from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.api import api_router
from core.config import settings
from db.redis import redis_connector
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
