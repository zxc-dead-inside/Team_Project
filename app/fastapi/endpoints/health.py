from datetime import UTC, datetime

import httpx
from core.config import settings

from fastapi import APIRouter


router = APIRouter()


@router.get("/")
async def health_check():
    """Health check endpoint for the API"""
    health = {"status": "ok", "services": {"fastapi": {"status": "ok"}}}

    # Check Auth service
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{settings.auth_service_url}/api/health")
            if response.status_code == 200:
                health["services"]["auth"] = {
                    "status": "healthy",
                    "timestamp": datetime.now(UTC),
                }
            else:
                health["services"]["auth"] = {
                    "status": "degraded",
                    "message": "Unexpected response",
                }
                health["status"] = "degraded"
    except Exception as e:
        health["services"]["auth"] = {"status": "down", "message": str(e)}
        health["status"] = "degraded"

    return health
