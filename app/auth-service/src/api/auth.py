from fastapi import APIRouter
from src.api.v1 import auth

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
auth_router.include_router(auth.private_router)
auth_router.include_router(auth.public_router)
