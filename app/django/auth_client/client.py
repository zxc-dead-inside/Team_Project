import logging
import threading
from datetime import UTC, datetime, timezone
from typing import Any

import httpx
import jwt
import redis

from django.conf import settings


logger = logging.getLogger(__name__)


class AuthServiceClient:
    """Client for communicating with the Auth service."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AuthServiceClient, cls).__new__(cls)
                cls._instance.base_url = settings.AUTH_SERVICE_URL
                cls._instance.timeout = settings.AUTH_SERVICE_TIMEOUT
                cls._instance.public_key = None
                cls._instance.public_key_expiry = None
                cls._instance._redis_client = None
        return cls._instance

    @property
    def redis_client(self):
        """Lazy initialize Redis client."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis.from_url(settings.REDIS_URL)
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis_client = None
        return self._redis_client

    def _get_public_key(self) -> str:
        """Get public key from auth service or cache."""
        if self.redis_client:
            cached_key = self.redis_client.get("auth_service_public_key")
            if cached_key:
                return cached_key.decode()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/v1/auth/public-key")
                response.raise_for_status()
                public_key = response.json()["public_key"]

                # Cache the public key for 1 day
                if self.redis_client:
                    self.redis_client.setex(
                        "auth_service_public_key", 86400, public_key
                    )
                return public_key
        except Exception as e:
            logger.error(f"Failed to get public key: {e}")
            # Return cached key even if expired as fallback
            if self.redis_client:
                cached_key = self.redis_client.get("auth_service_public_key")
                if cached_key:
                    return cached_key.decode()
            raise

    def validate_token(
        self, token: str, token_type: str = "access"
    ) -> tuple[bool, dict[str, Any] | None]:
        """Validate JWT token with Auth service or locally if service unavailable."""
        try:
            # First try to validate with auth service
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/v1/auth/validate-token",
                    json={"token": token, "type": token_type},
                )
                response.raise_for_status()
                return True, response.json().get("user_data")
        except httpx.RequestError as e:
            logger.warning(
                f"Auth service unavailable, falling back to local validation: {e}"
            )
            # Fallback to local validation
            return self._validate_token_locally(token, token_type)
        except httpx.HTTPStatusError as e:
            logger.error(f"Auth service rejected token: {e}")
            return False, None

    def _validate_token_locally(
        self, token: str, token_type: str = "access"
    ) -> tuple[bool, dict[str, Any] | None]:
        """Validate JWT token locally using cached public key."""
        try:
            public_key = self._get_public_key()
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_signature": True},
            )

            if payload.get("type") != token_type:
                logger.warning(
                    f"Token type mismatch: expected {token_type}, got {payload.get('type')}"
                )
                return False, None

            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.now(UTC) > datetime.fromtimestamp(exp, tz=timezone.utc):
                return False, None

            # Check if token is in blacklist (if redis is available)
            if self.redis_client:
                try:
                    is_blacklisted = self.redis_client.exists(
                        f"blacklisted_token:{token}"
                    )
                    if is_blacklisted:
                        return False, None
                except redis.RedisError:
                    # If redis is unavailable, continue with degraded service
                    logger.warning("Redis unavailable for blacklist check")

            return True, payload
        except jwt.PyJWTError as e:
            logger.error(f"Failed to locally validate token: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error during local token validation: {e}")
            return False, None

    def login(self, username: str, password: str) -> dict[str, str] | None:
        """Login to Auth service."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    data={"username": username, "password": password},
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.error(f"Login error: {e}")
            return None

    def refresh_token(self, refresh_token: str) -> dict[str, str] | None:
        """Refresh access token using refresh token."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/v1/auth/refresh",
                    headers={"Authorization": f"Bearer {refresh_token}"},
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
