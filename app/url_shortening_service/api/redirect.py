from typing import Annotated

from core.logging import get_logger
from services.url_service import URLService

from api.dependencies import get_url_service
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse


logger = get_logger(__name__)
router = APIRouter()

@router.get("/{short_code}")
async def redirect_url(
    short_code: str,
    request: Request,
    url_service: Annotated[URLService, Depends(get_url_service)]
):
    """Redirect to original URL and log analytics"""
    try:
        client_info = {
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer")
        }

        original_url = await url_service.get_original_url(short_code, client_info)

        logger.info("Redirecting", short_code=short_code, original_url=original_url)
        return RedirectResponse(url=original_url, status_code=302)

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail="URL not found")
        elif "expired" in error_msg:
            raise HTTPException(status_code=410, detail="URL expired")
        else:
            raise HTTPException(status_code=400, detail=error_msg)

redirect_router = router
