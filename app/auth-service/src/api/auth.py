from fastapi import APIRouter

from src.api.v1.login import router as login_router

auth_router = APIRouter()

auth_router.include_router(login_router, prefix="/auth", tags=["Auth"])