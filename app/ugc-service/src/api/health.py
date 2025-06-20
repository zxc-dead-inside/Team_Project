from fastapi import APIRouter
from ..database import get_database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        db = get_database()
        await db.command("ping")
        return {
            "status": "healthy",
            "service": "UGC Service",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "UGC Service",
            "database": "disconnected",
            "error": str(e)
        } 