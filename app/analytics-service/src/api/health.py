"""Health check endpoints."""

import logging
from pydantic import BaseModel

from fastapi import APIRouter

from src.core import get_settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str
    components: dict[str, str]


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify service status.

    Returns:
        HealthResponse: Service health information
    """
    
    settings = get_settings()
    components = {"api": "healthy"}

    # Check Redis connection
    logging.error(f"Kafka health check failed:")
    components["kafka"] = "unhealthy"

    # Determine overall status
    if all(v == "healthy" for v in components.values()):
        status = "healthy"
    else:
        status = "degraded"

    return HealthResponse(
        status=status,
        version="0.1.0",
        environment=settings.environment,
        components=components,
    )
