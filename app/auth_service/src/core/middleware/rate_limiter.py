import logging
import time
from collections.abc import Awaitable, Callable
from uuid import NAMESPACE_DNS, uuid5

from dependency_injector.wiring import Provide
from src.core.container import Container
from src.core.logger import setup_logging
from src.services.auth_service import AuthService
from src.services.redis_service import RedisService
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer


setup_logging()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="LoginRequest",
    auto_error=False
)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting. This middleware
    checks how many requests a user can make based on their role and
    the time since the last token recharge.
    """

    def __init__(
            self,
            app: FastAPI,
            unlimited_roles: set[str],
            special_roles: set[str],
            special_capacity: int,
            default_capacity: int,
            undefind_capacity: int
    ):
        """
        Initialize RateLimiterMiddleware.

        Args:
            app: FastAPI application instance.
            unlimited_roles: User roles that are not rate limited.
            special_roles: Roles with special rights to limit the rate.
            special_capacity: Number of requests for users with special roles.
            default_capacity: Default number of requests for other users.
            undefind_capacity: Number of requests for users with no role or with an unrecognized role.

        Returns:
            RateLimiterMiddleware
        """

        super().__init__(app)
        self.unlimited_roles = unlimited_roles
        self.special_roles = special_roles
        self.special_capacity = special_capacity
        self.default_capacity = default_capacity
        self.undefind_capacity = undefind_capacity

    async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
            auth_service: AuthService = Provide[Container.auth_service]
    ):
        """
        Processes incoming HTTP requests using rate limiting logic.
        Checks the token, determines the user's role, and based on that,
        decides how many requests the user can make.

        Args:
            request: The incoming HTTP request.
            call_next: The function to pass control to the next request handler.
            auth_service [Dependecy]: The service to handle token decoding.

        Returns:
            Response from the next middleware or 429 HTTP code if rate limit exceeded.
        """

        key = str(uuid5(NAMESPACE_DNS, str(request.client.host)))
        capacity = self.undefind_capacity
        token: str = await oauth2_scheme(request=request)

        if token:
            try:
                payload = await auth_service.decode_token(token=token)
                roles = (payload.get('roles', None))
                if roles & self.unlimited_roles:
                    return await call_next(request)

                key = payload.get('sub')
                capacity = self.default_capacity
                if roles & self.special_roles:
                    capacity = self.special_capacity

            except Exception as exc:
                logging.debug(exc)

        if await self.take_token(key=key, capacity=capacity):
            return await call_next(request)
        return JSONResponse(
            status_code=429, content={'detail': 'Rate limit exceeded'})

    async def take_token(
            self,
            key,
            capacity,
            redis_service: RedisService = Provide[Container.redis_service]
    ) -> bool:
        """
        Attempt to take a token from a bucket while maintaining an
        rate limit given the time since the last token refresh.
        https://en.wikipedia.org/wiki/Token_bucket

        Args:
            key: Unique user or client identifier.
            capacity: Maximum token bucket capacity for the user.
            redis_service: Service for working with Redis.
        
        Returns:
            True if the request can be fulfilled (token available), False if the limit is exceeded.
        """

        # Ensure the bucket is refilled based on the elapsed time
        refill_rate = capacity / 60
        now = time.time()
        # Add tokens to the bucket based on the time elapsed since the last refill

        async with redis_service.redis_client.lock(key, timeout=0.05):
            tokens = await redis_service.get(key=f'tokens:{key}')
            if not tokens:
                await redis_service.set(
                    key=f'tokens:{key}', value=capacity - 1)
                await redis_service.set(key=f'last_refill:{key}', value=now)
                return True

            tokens = float(tokens)
            last_refill = float(
                await redis_service.get(key=f'last_refill:{key}'))

            if tokens < capacity:
                # Calculate the number of tokens to add
                tokens_to_add = (now - last_refill) * refill_rate
                # Update the token count, ensuring it doesn't exceed the capacity
                tokens = min(capacity, tokens + tokens_to_add)

            await redis_service.set(key=f'last_refill:{key}', value=now)
            logging.debug(
                f'Tokens: {tokens}, Last refill: {last_refill} Key: {key}')
            if tokens >= 1:
                # Deduct a token for the API call
                await redis_service.set(key=f'tokens:{key}', value=tokens - 1)
                return True  # Indicate that the API call can proceed
            return False  # Indicate that the rate limit has been exceeded
