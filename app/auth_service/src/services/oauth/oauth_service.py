import base64
import secrets
from collections.abc import Callable

from src.db.repositories.user_repository import UserRepository
from src.services.oauth.base import BaseOAuthProvider
from src.services.redis_service import RedisService
from starlette import status

from fastapi import HTTPException


class OAuthError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class OAuthService:
    def __init__(
        self,
        provider_factory: dict[str, Callable[[], BaseOAuthProvider]],
        redis_service: RedisService,
        user_repository: UserRepository,
        state_ttl: int,
    ):
        self.provider_factory = provider_factory
        self.redis_service = redis_service
        self.user_repo = user_repository
        self.state_ttl = state_ttl

    async def save_state(
            self, provider: str, state: str, ttl: int = 60) -> str:
        await self.redis_service.set(f"{provider}:oauth:", state, ttl)

    async def validate_state(self, provider: str, state: str) -> bool:
        return await self.redis_service.exists(f"{provider}:oauth:{state}")
    
    @staticmethod
    def generate_state(length: int = 32):
        token_bytes = secrets.token_bytes(length)
        token = base64.urlsafe_b64encode(token_bytes).decode().rstrip("=")
        return token 