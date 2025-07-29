from fastapi import APIRouter

from src.api.v1.notifications import router as notification_router

api_router = APIRouter()

api_router.include_router(
    notification_router,
    prefix="/api/v1/notify",
    tags=["WebSocket Notifications"]
)