from fastapi import APIRouter

from .endpoints.urls import router as urls_router


api_router = APIRouter()
api_router.include_router(urls_router, prefix="/urls", tags=["urls"])