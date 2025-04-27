"""Metrics endpoints."""

import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Request, BackgroundTasks, Depends

from src.core.container import Container
from src.models.metrics import MetricResponse, MetricRequest
from src.services.kafka.producer import KafkaProducer


router = APIRouter()


@router.post("/metrics", status_code=200)
@inject
async def push_metrics(
    metrics: MetricRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    kafka_producer: KafkaProducer = Depends(Provide[Container.kafka_producer]),
    kafka_topic: str = Depends(Provide[Container.config.kafka_topic])
) -> MetricResponse:
    """
    Metrics endpoint to receive user activity and send to Kafka.

    Returns:
        MetricResponse: Metrics received information
    """

    logging.debug(f'Recieved metrics from {request.client.host}: {metrics}')
    background_tasks.add_task(
        kafka_producer.send_and_wait,
        kafka_topic,
        value=metrics.model_dump_json().encode('utf-8')
    )

    raw_body = await request.body()
    return MetricResponse(status='ok', receivded=len(raw_body))
