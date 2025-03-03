# src/services/email_service.py
"""Email service for sending confirmation emails."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pydantic import EmailStr


logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending confirmation emails and managing tokens."""

    def __init__(
        self,
        secret_key: str,
        email_token_ttl_seconds: int = 600,
    ):
        """Initialize the email service."""
        self.secret_key = secret_key
        self.email_token_ttl_seconds = email_token_ttl_seconds

    def create_confirmation_token(self, user_id: str, email: str) -> str:
        """Create an email confirmation token."""
        expires_delta = timedelta(seconds=self.email_token_ttl_seconds)
        expire = datetime.now(UTC) + expires_delta

        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "type": "email_confirmation",
        }

        return jwt.encode(to_encode, self.secret_key, algorithm="HS256")

    def validate_confirmation_token(
        self, token: str
    ) -> tuple[bool, dict[str, Any] | None]:
        """Validate an email confirmation token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            # Check token type
            if payload.get("type") != "email_confirmation":
                return False, None

            return True, payload
        except JWTError as e:
            logger.error(f"Token validation error: {e}")
            return False, None

    async def send_confirmation_email(self, email: EmailStr, token: str) -> bool:
        """Send a confirmation email (mock implementation)."""
        # Mock implementation - in production this would send a real email
        confirmation_url = f"/api/v1/auth/confirm-email?token={token}"
        logger.info(f"[MOCK EMAIL] To: {email}, Subject: Confirm your account")
        logger.info(
            f"[MOCK EMAIL] Body: Please confirm your account by clicking: {confirmation_url}"
        )

        # Return True to simulate successful sending
        return True
