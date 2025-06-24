"""Metrics endpoints."""

from dependency_injector.wiring import Provide, inject
from src.core.container import Container
from src.models.metrics import UserAction

from fastapi import APIRouter, BackgroundTasks, Depends


router = APIRouter()


@router.post("/action")
@inject
async def record_action(
    action: UserAction,
    background_tasks: BackgroundTasks,
    event_sender=Depends(Provide[Container.event_sender]),
):
    """
    Endpoint to submit user action events.

    Args:
        event: Validated user action event
        background_tasks: FastAPI background tasks manager

    Returns:
        dict: Status message

    Raises:
        HTTPException: 400 for validation errors, 500 for server errors
    """

    background_tasks.add_task(event_sender.send_event, action.model_dump())
    return {"status": "queued"}
