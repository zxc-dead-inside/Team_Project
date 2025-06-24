"""JWT Bearer implementation with anonymous user support."""

import contextlib
import http
import json
import logging
import time
import uuid
from typing import Any

import httpx
import jwt
import redis
from core.config import settings
from models.auth import RoleModel, Roles, UserData

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer


logger = logging.getLogger(__name__)


class JWTBearer(HTTPBearer):
    """JWT bearer authentication with anonymous user support."""

    def __init__(self, auto_error: bool = True, require_auth: bool = False):
        """
        Initialize the JWT Bearer authentication.

        Args:
            auto_error: Whether to auto-error on missing credentials
            require_auth: If True, only authenticated users are allowed (no anonymous)
        """
        super().__init__(auto_error=auto_error)
        self.require_auth = require_auth
        self.public_key = None
        self.public_key_expiry = None

        try:
            self.redis = redis.Redis.from_url(
                settings.redis_url, socket_timeout=1, socket_connect_timeout=1
            )
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis = None

    async def get_public_key(self) -> str:
        """Get public key from Redis cache or Auth service."""
        if self.redis:
            try:
                cached_key = self.redis.get("auth_service_public_key")
                if cached_key:
                    return cached_key.decode()  # type: ignore[union-attr]
            except redis.RedisError:
                logger.warning("Redis unavailable for public key cache")

        try:
            async with httpx.AsyncClient(
                timeout=settings.auth_service_timeout
            ) as client:
                response = await client.get(
                    f"{settings.auth_service_url}/api/v1/auth/public-key"
                )
                response.raise_for_status()
                public_key = response.json().get("public_key")

                if self.redis:
                    with contextlib.suppress(redis.RedisError):
                        self.redis.setex("auth_service_public_key", 86400, public_key)

                return public_key
        except Exception as e:
            logger.error(f"Failed to get public key from Auth service: {e}")

            if self.redis:
                try:
                    emergency_mode = self.redis.get("auth_service_emergency_mode")
                    emergency_key = self.redis.get("auth_service_emergency_key")
                    if emergency_mode and emergency_key:
                        logger.warning("Using emergency public key for validation")
                        return emergency_key.decode()  # type: ignore[union-attr]
                except redis.RedisError:
                    pass

            # no Redis and no Auth service, out of options
            raise HTTPException(
                status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Authentication service is unavailable",
            )

    def get_token_expiry(self, payload: dict) -> int:
        """Extract token expiration time and convert to TTL."""
        exp = payload.get("exp", 0)
        now = int(time.time())
        return max(exp - now, 60)

    async def get_cached_roles(self, user_id: str) -> list[str] | None:
        """Get cached user roles from Redis."""
        if not self.redis:
            return None

        try:
            cached_roles = self.redis.get(f"user_roles:{user_id}")
            if cached_roles:
                return json.loads(
                    cached_roles.decode()  # type: ignore[union-attr]
                )
        except Exception as e:
            logger.warning(f"Failed to get cached roles: {e}")

        return None

    async def cache_roles(
            self, user_id: str, roles: list[str], ttl: int | None = None
    ):
        """Cache user roles in Redis with proper TTL."""
        if not self.redis:
            return

        if ttl is None:
            ttl = settings.token_blacklist_ttl

        try:
            self.redis.setex(f"user_roles:{user_id}", ttl, json.dumps(roles))
        except Exception as e:
            logger.warning(f"Failed to cache roles: {e}")

    async def validate_token_locally(
        self, token: str, token_type: str = "access"
    ) -> dict[str, Any]:
        """Validate token locally using cached public key."""
        try:
            public_key = await self.get_public_key()

            payload = jwt.decode(
                token, public_key, algorithms=["RS256"], options={"verify_exp": True}
            )

            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=http.HTTPStatus.UNAUTHORIZED,
                    detail=f"Invalid token type: expected {token_type}, got {payload.get('type')}",
                )

            if self.redis:
                try:
                    if self.redis.exists(f"blacklisted_token:{token}"):
                        raise HTTPException(
                            status_code=http.HTTPStatus.UNAUTHORIZED,
                            detail="Token has been revoked",
                        )
                except redis.RedisError:
                    logger.warning("Redis unavailable for blacklist check")

            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED, detail="Token has expired"
            ) from None
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            ) from e

    async def get_anonymous_user(self, request: Request) -> UserData:
        """Create anonymous user data matching auth service behavior."""
        client_ip = request.client.host if request.client else "unknown"

        cache_key = f"anonymous_user:{client_ip}"
        if self.redis:
            try:
                cached_user = self.redis.get(cache_key)
                if cached_user:
                    user_data = json.loads(
                        cached_user.decode()  # type: ignore[union-attr]
                    )
                    return self._convert_to_user_data(user_data)
            except redis.RedisError:
                logger.warning("Redis unavailable for anonymous user cache")

        try:
            async with httpx.AsyncClient(
                timeout=settings.auth_service_timeout
            ) as client:
                headers = {"X-Forwarded-For": client_ip}
                response = await client.get(
                    f"{settings.auth_service_url}/api/v1/users/public", headers=headers
                )
                response.raise_for_status()
                user_data = response.json()

                if self.redis:
                    with contextlib.suppress(redis.RedisError):
                        self.redis.setex(cache_key, 3600, json.dumps(user_data))

                return self._convert_to_user_data(
                    {
                        "id": user_data.get("user_id", ""),
                        "username": user_data.get("username", "anonymous"),
                        "email": "anonymous@example.com",
                        "is_superuser": False,
                        "roles": user_data.get("roles", ["anonymous"]),
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to get anonymous user from auth service: {e}")

            anonymous_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, client_ip))
            anonymous_role = Roles.get_roles()[Roles.ANONYMOUS]
            fallback_user = UserData(
                id=anonymous_uuid,
                username=f"anonymous_{client_ip}",
                email="anonymous@example.com",
                is_superuser=False,
                roles=[anonymous_role],
            )

            return fallback_user

    async def __call__(self, request: Request) -> UserData:
        """Extract and validate JWT token from request, or return anonymous user."""
        token = None

        try:
            credentials = await super().__call__(request)
            if credentials and credentials.scheme.lower() == "bearer":
                token = credentials.credentials
        except HTTPException:
            token = None

        if token:
            try:
                user_data = await self.validate_token(token)

                if self.require_auth:
                    user_roles = [role.name for role in user_data.roles]
                    if "anonymous" in user_roles:
                        raise HTTPException(
                            status_code=http.HTTPStatus.UNAUTHORIZED,
                            detail="Authentication required",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                return user_data
            except HTTPException:
                if self.require_auth:
                    raise
                return await self.get_anonymous_user(request)
        else:
            if self.require_auth:
                raise HTTPException(
                    status_code=http.HTTPStatus.UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return await self.get_anonymous_user(request)

    async def validate_token(self, token: str, token_type: str = "access") -> UserData:
        """Validate token with Auth service or locally if service unavailable."""
        try:
            async with httpx.AsyncClient(
                timeout=settings.auth_service_timeout
            ) as client:
                response = await client.post(
                    f"{settings.auth_service_url}/api/v1/auth/validate-token",
                    json={"token": token, "type": token_type},
                )
                response.raise_for_status()
                user_data = response.json().get("user_data", {})

                if "id" in user_data and "roles" in user_data:
                    user_id = user_data["id"]
                    roles = [role.get("name") for role in user_data.get("roles", [])]

                    try:
                        payload = jwt.decode(token, options={"verify_signature": False})
                        ttl = self.get_token_expiry(payload)
                    except Exception:
                        ttl = settings.token_blacklist_ttl

                    await self.cache_roles(user_id, roles, ttl)

                return self._convert_to_user_data(user_data)
        except httpx.RequestError as e:
            logger.warning(
                f"Auth service unavailable, falling back to local validation: {e}"
            )
            payload = await self.validate_token_locally(token, token_type)
            return self._convert_to_user_data(payload)

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get("detail", str(e))
            except Exception:
                error_detail = f"Auth service error: {str(e)}"

            logger.error(f"Auth service rejected token: {error_detail}")
            raise HTTPException(
                status_code=(
                    status_code
                    if 400 <= status_code < 500
                    else http.HTTPStatus.UNAUTHORIZED
                ),
                detail=error_detail,
            ) from e

    def _convert_to_user_data(self, data: dict) -> UserData:
        """Convert dictionary user data to Pydantic model."""
        roles_data = data.get("roles", [])
        roles = []
        for role in roles_data:
            if isinstance(role, dict):
                roles.append(RoleModel(**role))
            else:
                role_name = role
                standard_roles = Roles.get_roles()
                if role_name in standard_roles:
                    roles.append(standard_roles[role_name])
                else:
                    roles.append(RoleModel(name=role_name))

        return UserData(
            id=data.get("id", ""),
            username=data.get("username", ""),
            email=data.get("email", ""),
            is_superuser=data.get("is_superuser", False),
            roles=roles,
        )
