from datetime import datetime, UTC
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, FastAPI
from typing import Callable, Awaitable
from starlette.responses import Response
from jose import JWTError

from src.services.auth_service import AuthService


class AnonymousUserMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks the user by token and assigns an anonymous role
    if the token is not valid.
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        auth_service: AuthService = request.app.container.auth_service()
        token = request.headers.get("Authorization")

        user = None
        if token and token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
            try:
                user = await auth_service.validate_token(token)
            except JWTError:
                user = None

        if not user:
            user = request.app.state.anonymous_user

        request.state.user = user
        response = await call_next(request)
        return response
