from datetime import datetime, UTC
from uuid import uuid4, uuid5, NAMESPACE_DNS

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, FastAPI
from typing import Callable, Awaitable
from starlette.responses import Response
from jose import JWTError

from src.services.auth_service import AuthService
from src.services.role_service import RoleService
from src.db.models import User, Role


class AnonymousUserMiddleware(BaseHTTPMiddleware):
    """
    Middleware, который проверяет пользователя по токену и, если токен отсутствует
    или невалиден, создаёт уникального анонимного пользователя на основе IP.
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        auth_service: AuthService = request.app.container.auth_service()
        role_service: RoleService = request.app.container.role_service()
        token = request.headers.get("Authorization")

        user = None
        if token and token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
            try:
                user = await auth_service.validate_token(token)
            except JWTError:
                user = None

        if not user:
            user_ip = request.client.host if request.client else "unknown"
            anonymous_uuid = str(uuid5(NAMESPACE_DNS, user_ip))

            user = User(
                id=anonymous_uuid,
                username=f"anonymous_{user_ip}",
                email="anonymous@example.com",
                password="*"*256,
                is_active=False,
                is_superuser=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            anonymous_role = await role_service.get_role_by_name("anonymous")
            if anonymous_role:
                user.roles.append(anonymous_role)

        request.state.user = user
        response = await call_next(request)
        return response
