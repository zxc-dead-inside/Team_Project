from fastapi import APIRouter

from src.api.v1.login import private_router
from src.api.v1.login import public_router

auth_router = APIRouter()

auth_router.include_router(
    private_router, prefix="/auth", tags=["Authentication"])
auth_router.include_router(
    public_router, prefix="/auth", tags=["Authentication"])