import httpx

from src.services.oauth.base import BaseOAuthProvider

class YandexOAuthProvider(BaseOAuthProvider):
    async def get_user_data(self, tokens: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url,
                params={"format": "json", "oauth_token": tokens["access_token"]}
            )
            data = response.json()
            return {
                "provider_id": data["id"],
                "email": data.get("default_email"),
                "username": data["login"]
            }

class VKOAuthProvider(BaseOAuthProvider):
    async def get_user_data(self, tokens: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url,
                params={
                    "access_token": tokens["access_token"],
                    "v": "5.131",
                    "fields": "email",
                }
            )
            data = response.json()["response"][0]
            return {
                "provider_id": str(data["id"]),
                "email": tokens.get("email"),
                "username": f"vk_{data['id']}"
            }