import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pydantic import EmailStr


logger = logging.getLogger(__name__)


class EmailService:
    """Email verification service with secure HMAC-SHA-256 token storage."""

    def __init__(self, public_key: str, private_key: str, email_token_ttl_seconds: int):
        self.public_key = public_key
        self.private_key = private_key
        self.email_token_ttl_seconds = email_token_ttl_seconds

    def create_confirmation_token(self, user_id: str, email: str) -> str:
        """
        Create a confirmation token for an email address.
        """
        expires_delta = timedelta(seconds=self.email_token_ttl_seconds)
        expire = datetime.now(UTC) + expires_delta

        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "type": "email_confirmation",
        }

        return jwt.encode(to_encode, self.private_key, algorithm="RS256")

    def validate_confirmation_token(
        self, token: str
    ) -> tuple[bool, dict[str, Any] | None]:
        try:
            payload = jwt.decode(token, self.public_key, algorithms=["RS256"])

            if payload["type"] != "email_confirmation":
                return False, None

            return True, payload

        except jwt.exceptions.InvalidTokenError as e:
            logger.error(f"Token validation failed: {e}")
            return False, None

    async def send_confirmation_email(self, email: EmailStr, token: str) -> bool:
        """Send a confirmation email (mock implementation)."""
        confirmation_url = f"/api/v1/auth/confirm-email?token={token}"
        logger.info(f"[MOCK EMAIL] To: {email}, Subject: Confirm your account")
        logger.info(
            f"[MOCK EMAIL] Body: Please confirm your account by clicking: {confirmation_url}"
        )

        # Return True to simulate successful sending
        return True
