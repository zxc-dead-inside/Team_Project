from pydantic import BaseModel

from fastapi import APIRouter, Depends
from fastapi.requests import Request


from src.services.di import get_login_service
from src.services.login import LoginService


class TokenResponse(BaseModel):
    status: int

class User(BaseModel):
    name: str

class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str
    components: dict[str, str]

router = APIRouter()

@router.get("/login", response_model=None)
async def login(
        request: Request,
        login_service: LoginService = Depends(get_login_service)
    ):
    """
    Login endpoint for user authorization.

    Returns:
        LoginResponse: User`s Access and Refresh tokens.
    """

    return 200