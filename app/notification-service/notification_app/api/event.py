from fastapi import APIRouter, HTTPException, status

from notification_app.schemas.event import (IncomingEvent, FixedEvent,
                                            BroadcastMessage, PersonalizedBatch)
from notification_app.services.notification_service import NotificationService
from notification_app.core.logger import logger

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/custom")
async def handle_custom_event(event: IncomingEvent):
    try:
        message = await NotificationService.handle_custom_event(event)
        return {"status": "queued", "message": message}
    except Exception as e:
        logger.exception("Error sending custom event to Kafka")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing event")


@router.post("/fixed")
async def handle_fixed_event(event: FixedEvent):
    try:
        message = await NotificationService.handle_fixed_event(event)
        return {"status": "queued", "message": message}
    except Exception as e:
        logger.exception("Error sending fixed event to Kafka")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing event")


@router.post("/broadcast")
async def send_broadcast(msg: BroadcastMessage):
    try:
        message = await NotificationService.send_broadcast(msg)
        return {"status": "queued", "message": message}
    except Exception as e:
        logger.exception("Error sending broadcast event to Kafka")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing event")


@router.post("/personalized")
async def send_personalized(batch: PersonalizedBatch):
    try:
        count = await NotificationService.send_personalized(batch)
        return {"status": "queued", "count": count}
    except Exception as e:
        logger.exception("Error sending personalized events to Kafka")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing event")