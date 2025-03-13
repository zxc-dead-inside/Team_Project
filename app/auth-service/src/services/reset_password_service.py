import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr

from src.db.repositories.user_repository import UserRepository
from src.services.redis_service import RedisService
from src.core.logger import setup_logging

setup_logging()


class ResetPasswordService:
    """Service for reset password operations."""

    password_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

    def __init__(
            self, user_repository: UserRepository,
            reset_token_ttl: int, max_requests_per_ttl: int,
            secret_key: str, cache_service: RedisService
    ):
        self.user_repository = user_repository
        self.reset_token_ttl = reset_token_ttl
        self.max_requests_per_ttl = max_requests_per_ttl
        self.secret_key = secret_key
        self.cache_service = cache_service

    async def __get_request_number(self, key: str) -> int | None:
        """
        Returns request number
        
        Args:
            key for lookup up in cache

        Retruns:
            Amount of requests to get reset token.
        """

        value = await self.cache_service.get(key)
        if value is None:
            current_requests = 0
        elif value.isdigit():
            current_requests = int(value)
        else:
            return None
        
        return current_requests

    
    async def check_requests(
            self, email: EmailStr
    ) -> tuple[bool, str | None]:
        """
        Checks if amount of request reaches the limit.
        
        Args:
            User email
        
        Returns:
            bool: False if limit was exceeded or lack result
            str: message if limit was exceeded
        """

        key = f"forgot_password:{email}"
        current_requests = await self.__get_request_number(key)

        if current_requests is None:
            return False, None

        if current_requests > self.max_requests_per_ttl:
            return False, "Too many attempts. Please try again later."
        
        return True, None
    
    async def increase_requests(
            self, email: EmailStr
    ) -> tuple[bool, str | None]:
        """
        Increses amount of requests.
        
        Args: email

        Returns:
            bool: True if operation was successful
            str: message if operation was not successful
        """

        key = f"forgot_password:{email}"
        current_requests = await self.__get_request_number(key)
        if current_requests is None:
            return False, "Unexpected Error"

        current_requests += 1

        await self.cache_service.set(
            key, current_requests, self.reset_token_ttl)
        
        return True, None

    def create_reset_token(self, user_id: UUID, email: EmailStr) -> str:
        """
        Create a reset token for an email address.
        
        Args:
           User ID and user email

        Reterns:
            JWT token
        """

        expires_delta = timedelta(seconds=self.reset_token_ttl)
        expire = datetime.now(UTC) + expires_delta

        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "type": "reset_token",
        }

        return jwt.encode(to_encode, self.secret_key, algorithm="HS256")
    
    def validate_reset_token(
            self, token: str
    ) -> tuple[bool, dict[str, Any] | None]:
        """
        Validates reset token.

        Args: JWT token

        Returns:
            True and payload if token is valid, False and None in otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            if payload["type"] != "reset_token":
                return False, None

            return True, payload

        except JWTError as e:
            logging.error(f"Token validation failed: {e}")
            return False, None

    def hash_password(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain password
            
        Returns:
            str: Hashed password
        """
        return self.password_context.hash(password)

    async def reset_password(
            self, token: str, password: str
    ) -> tuple[bool, str]:
        """
        Reset a password if token is valid, user exists, email is correct and
        password was validated.

        Args:
            token: user token
            password: new user password

        Returns: tuple(bool, str)
            bool: True if password was changed or Fals if was not
            str: Message with details

        """

        is_valid, payload = self.validate_reset_token(token)
        
        if not is_valid:
            return False, "Invalid or expired token"
        
        user_id = payload.get("sub")
        email = payload.get("email")

        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return False, "User not found"

        if user.email != email:
            return False, "Email mismatch"
        
        user.password = self.hash_password(password)
        await self.user_repository.update(user)
        
        return True, "Your password has been changed."

    async def send_reset_password_email(
        self, email: EmailStr, token: str
    ) -> bool:
        """
        Send an email with reset token.
        
        Args:
            email: user email
            token: jwt token
        """

        confirmation_url = f"/api/v1/auth/confirm-email?token={token}"

        logging.info(f"[MOCK EMAIL] To: {email}, Subject: Reset your password")
        logging.info(
            "[MOCK EMAIL] Body: Someone has requested a password reset for "
            f"your account. You can use this link to reset your password: "
            f"{confirmation_url}"
        )

        return True    
