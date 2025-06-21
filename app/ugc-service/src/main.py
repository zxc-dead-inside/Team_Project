from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.database import connect_to_mongo, close_mongo_connection
from src.api import bookmarks, likes, reviews, health

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(bookmarks.router, prefix=settings.api_v1_prefix)
app.include_router(likes.router, prefix=settings.api_v1_prefix)
app.include_router(reviews.router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    await close_mongo_connection()


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "UGC Service API",
        "version": settings.version,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    ) 