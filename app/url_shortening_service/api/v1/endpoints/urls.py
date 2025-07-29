from typing import Annotated

from core.logging import get_logger
from schemas.url import URLCreateRequest, URLResponse, URLStats
from services.url_service import URLService

from api.dependencies import get_url_service
from fastapi import APIRouter, Depends, HTTPException


logger = get_logger(__name__)
router = APIRouter()

@router.post("/shorten", response_model=URLResponse)
async def shorten_url(
    request: URLCreateRequest,
    url_service: Annotated[URLService, Depends(get_url_service)]
):
    """Create a shortened URL"""
    try:
        return await url_service.create_short_url(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{short_code}", response_model=URLStats)
async def get_url_stats(
    short_code: str,
    url_service: Annotated[URLService, Depends(get_url_service)]
):
    """Get URL statistics"""
    try:
        return await url_service.get_url_stats(short_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="URL not found")

@router.delete("/{short_code}")
async def deactivate_url(
    short_code: str,
    url_service: Annotated[URLService, Depends(get_url_service)]
):
    """Deactivate a shortened URL"""
    success = await url_service.deactivate_url(short_code)
    if not success:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"message": "URL deactivated successfully"}