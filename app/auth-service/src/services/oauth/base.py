
import httpx
from abc import ABC, abstractmethod


class BaseOAuthProvider(ABC):
    def __init__(
            self, config: dict):
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.redirect_uri = config["redirect_uri"]
        self.auth_url = config["auth_url"]
        self.token_url = config["token_url"]
        self.user_info_url = config["user_info_url"]

    async def get_auth_url(self, state: str) -> str:
        return (
            f"{self.auth_url}?client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&state={state}&"
            "response_type=code"
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

    @abstractmethod
    async def get_user_data(self, tokens: dict) -> dict:
        pass