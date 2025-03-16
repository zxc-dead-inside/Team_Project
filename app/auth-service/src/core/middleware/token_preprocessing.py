import jwt
import logging
from fastapi import FastAPI, Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Awaitable, Callable

from src.core.logger import setup_logging


setup_logging()


class TokenParser(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        public_key: str
    ):
        super().__init__(app)
        self.public_key = public_key

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        authorization = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)
        if authorization and scheme.lower() == 'bearer':
            try:
                request.state.user = jwt.decode(
                    token, self.public_key, algorithms=["RS256"])
            except jwt.ExpiredSignatureError:
                logging.warning(
                    f"Received a request with an expired token: {request}"
                )
            except jwt.InvalidTokenError:
                logging.warning(
                    f"Received a request with an invalid token: {request}"
                )
        return await call_next(request)
