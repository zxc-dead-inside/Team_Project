"""Health check endpoints."""

import logging

from pydantic import BaseModel
from src.api.decorators import requires_permissions
from src.core.config import get_settings
from src.db.database import Database
from src.services.redis_service import check_redis_connection

from fastapi import APIRouter
from fastapi.requests import Request


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str
    components: dict[str, str]


@router.get("", response_model=HealthResponse)
@requires_permissions(["healty_read"])
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint to verify service status.

    Returns:
        HealthResponse: Service health information
    """
    settings = get_settings()
    components = {"api": "healthy"}
    db_connector = Database(str(settings.database_url))

    # Check database connection
    try:
        db_healthy = await db_connector.check_connection()
        components["database"] = "healthy" if db_healthy else "unhealthy"
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        components["database"] = "unhealthy"

    # Check Redis connection
    try:
        redis_healthy = await check_redis_connection(str(settings.redis_url))
        components["redis"] = "healthy" if redis_healthy else "unhealthy"
    except Exception as e:
        logging.error(f"Redis health check failed: {e}")
        components["redis"] = "unhealthy"

    # Determine overall status
    status = (
        "healthy" if all(v == "healthy" for v in components.values()) else "degraded"
    )

    return HealthResponse(
        status=status,
        version="0.1.0",
        environment=settings.environment,
        components=components,
    )
