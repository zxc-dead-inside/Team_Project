"""Middleware for superuser permission handling with lazy dependency resolution."""

import logging
from typing import Awaitable, Callable

from src.core.logger import setup_logging
from src.db.repositories.audit_log_repository import AuditLogRepository
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi import FastAPI, Request, Response


setup_logging()


class SuperuserMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs superuser actions for auditing purposes.
    This version uses lazy dependency resolution to obtain the audit_log_repository
    at request time via a provided getter function.
    """

    def __init__(
        self,
        app: FastAPI,
        audit_log_repository_getter: Callable[[FastAPI], AuditLogRepository],
    ):
        """
        Initialize the middleware.

        Args:
            app: FastAPI application.
            audit_log_repository_getter: A callable that returns the audit_log_repository given the app.
        """
        super().__init__(app)
        self.audit_log_repository_getter = audit_log_repository_getter

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process a request and log superuser actions.

        Args:
            request: Request object.
            call_next: Function to call the next middleware.

        Returns:
            Response from the next middleware.
        """
        response = await call_next(request)

        user = getattr(request.state, "user", None)
        if user and getattr(user, "is_superuser", False):
            path = request.url.path
            method = request.method
            client_host = request.client.host if request.client else "unknown"

            logging.warning(
                f"Superuser action: {user.username} ({user.id}) - {method} {path} from {client_host}"
            )

            if not path.endswith(("/health", "/docs", "/redoc", "/openapi.json")):
                # Lazy fetch the repository from the app at request time
                audit_log_repository = self.audit_log_repository_getter(request.app)
                try:
                    await audit_log_repository.log_action(
                        action="superuser_action",
                        actor_id=user.id,
                        resource_type="api",
                        details={
                            "method": method,
                            "path": path,
                            "status_code": response.status_code,
                        },
                        ip_address=client_host,
                    )
                except Exception as e:
                    logging.error(f"Failed to log superuser action: {e}")

        return response
