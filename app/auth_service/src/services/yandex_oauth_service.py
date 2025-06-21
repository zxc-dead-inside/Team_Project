"""Service to authenticate through with Yandex account."""

import base64
import secrets

import httpx
from src.services.redis_service import RedisService


class YandexOAuthService:
    """Service to authenticate through with Yandex account."""

    def __init__(
            self,
            client_id: str,
            client_secret: str,
            redirect_uri: str,
            oauth_url: str,
            token_url: str,
            user_info_url: str,
            redis_service: RedisService
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.oauth_url = oauth_url
        self.token_url = token_url
        self.user_info_url = user_info_url
        self.redis_service = redis_service
    
    def get_auth_url(self, state: str) -> str:
        return (
            f"{self.oauth_url}?"
            f"response_type=code&"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"state={state}"
        )

    async def get_tokens(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url,
                params={"format": "json", "oauth_token": access_token}
            )
            response.raise_for_status()
            return response.json()

    async def save_state(self, state: str, ttl: int = 60) -> str:
        await self.redis_service.set("yandex:oauth:", state, ttl)

    async def validate_state(self, state) -> bool:
        return await self.redis_service.exists(f"yandex:oauth:{state}")
    
    @staticmethod
    def generate_state(length: int = 32):
        token_bytes = secrets.token_bytes(length)
        token = base64.urlsafe_b64encode(token_bytes).decode().rstrip("=")
        return token    
