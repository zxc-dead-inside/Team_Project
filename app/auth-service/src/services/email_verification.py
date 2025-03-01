import uuid
import hmac
import hashlib
from src.services.redis_service import RedisService
from src.core.config import Settings


async def send_msg(email, token):
    pass


class EmailVerifier:
    """Email verification service with secure HMAC-SHA-256 token storage."""

    def __init__(self, redis_service: RedisService, settings: Settings):
        self.redis = redis_service
        self.secret_key = settings.secret_key.encode()
        self.email_token_ttl = settings.email_token_ttl_seconds

    def hash_token(self, token: str) -> str:
        return hmac.new(
            self.secret_key, token.encode(), hashlib.sha256
        ).hexdigest()

    async def send_verification_email(self, email: str) -> str:
        token = str(uuid.uuid4())
        hashed_token = self.hash_token(token)
        await send_msg(email, token)
        await self.redis.set(
            f"email_verif:{hashed_token}",
            email,
            expire=self.email_token_ttl
        )

        return token

    async def verify_token(self, token: str) -> str | None:
        hashed_token = self.hash_token(token)
        email = await self.redis.get(f"email_verif:{hashed_token}")

        if email:
            await self.redis.delete(f"email_verif:{hashed_token}")
            return email

        return None
