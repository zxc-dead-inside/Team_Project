from typing import Callable, Awaitable
from uuid import uuid5, NAMESPACE_DNS


from dependency_injector.wiring import Provide, inject
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.core.container import Container
from src.core.token_bucket import TokenBucket
from src.services.auth_service import AuthService


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="LoginRequest",
    auto_error=False
)


class RateLimitterMiddleware(BaseHTTPMiddleware):
    @inject
    def __init__(
        self,
        app: FastAPI,
        unlimited_roles: set[str],
        special_roles: set[str],
        special_capacity: int,
        default_capacity: int,
        undefind_capacity: int,
        bucket: TokenBucket = Provide[Container.token_bucket]
    ):
        super().__init__(app)
        self.bucket = bucket
        self.unlimited_roles = unlimited_roles
        self.special_roles = special_roles
        self.special_capacity = special_capacity
        self.default_capacity = default_capacity
        self.undefind_capacity = undefind_capacity

    @inject
    async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
            auth_service: AuthService = Provide[Container.auth_service]
    ):  
        key = str(uuid5(NAMESPACE_DNS, str(request.client)))
        capacity=self.undefind_capacity
        token: str = await oauth2_scheme(request=request)
        if token:
            try:
                payload = await auth_service.decode_token(token=token)
                if set(payload.get('roles', None)) & self.unlimited_roles:
                    return await call_next(request)
                
                key = payload.get('sub')

                capacity = self.default_capacity
                if set(payload.get('roles', None)) & self.special_roles:
                    capacity = self.special_capacity
            except Exception:
                pass

        if await self.bucket.take_token(key=key, capacity=capacity):
            return await call_next(request)
        return JSONResponse(
            status_code=429, content={'detail': 'Rate limit exceeded'})
