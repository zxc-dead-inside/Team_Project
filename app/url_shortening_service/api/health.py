from core.settings import settings

from fastapi import APIRouter


router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }

health_router = router