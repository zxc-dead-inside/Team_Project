from fastapi import APIRouter

from src.api.v1.login import protected_router
from src.api.v1.login import public_router

auth_router = APIRouter()

auth_router.include_router(
    protected_router, prefix="/auth", tags=["Authentication"])
auth_router.include_router(
    public_router, prefix="/auth", tags=["Authentication"])