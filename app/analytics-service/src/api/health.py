"""Health check endpoints."""

import logging

from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel
from src.core.container import Container
from src.services.kafka.producer import KafkaProducer

from fastapi import APIRouter, Depends


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str
    components: dict[str, str]


@router.get("", response_model=HealthResponse)
@inject
async def health_check(
    environment: str = Depends(Provide[Container.config.environment]),
    kafka_producer: KafkaProducer = Depends(Provide[Container.kafka_producer]),
) -> HealthResponse:
    """
    Health check endpoint to verify service status.

    Returns:
        HealthResponse: Service health information
    """

    logging.debug("Healthcheck requested")
    components = {"api": "healthy"}

    # Check Kafka connection
    kafka_healthcheck = await kafka_producer.healthcheck()
    if kafka_healthcheck.get("status"):
        components["kafka"] = "healthy"
    else:
        components["kafka"] = "unhealthy"
        logging.error(f"Kafka health check failed: {kafka_healthcheck.get('detail')}")

    # Determine overall status
    if all(v == "healthy" for v in components.values()):
        status = "healthy"
    else:
        status = "degraded"

    return HealthResponse(
        status=status,
        version="0.1.0",
        environment=environment,
        components=components,
    )
