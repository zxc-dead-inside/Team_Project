from datetime import UTC, datetime

from api.api import api_router
from api.v1 import films

from core.config import settings
from db import elastic

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/api/openapi"
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event('startup')
async def startup():
    # Подключаемся к базам при старте сервера
    # Подключиться можем при работающем event-loop
    # Поэтому логика подключения происходит в асинхронной функции
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


@app.on_event('shutdown')
async def shutdown():
    # Отключаемся от баз при выключении сервера
    await elastic.es.close()


# app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(films.router, prefix='/api/v1/films', tags=['films'])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(UTC)}
