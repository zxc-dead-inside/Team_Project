import logging
import re

from fastapi import FastAPI, Request
from fastapi.routing import get_request_handler
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from uuid import UUID

from src.services.user_service import UserService
from src.core.logger import setup_logging

setup_logging()


# PUBLIC_PATTERNS = [
#     r"^/api/docs.*",
#     r"^/api/health",
#     r"^/openapi.json",
#     r"^/api/v1/auth/.*",
# ]


class PermissionMiddleware(BaseHTTPMiddleware):
    def __init__(
            self, app: FastAPI,
            user_service: UserService,
            secret_key: str
    ):
        super().__init__(app)
        self.user_service = user_service
        self.secret_key = secret_key

        # Public routes
        self.public_routes = [
            r"^/api/docs.*",
            r"^/api/health",
            r"^/openapi.json",
            r"^/api/v1/auth/.*",
        ]

        # Route permissions
        self.route_permissions = {
            "/roles/{role_id}": "role_read",
            "/movies": "movie_read",
        }

    async def dispatch(self, request: Request, call_next):

        logging.info("MIDDLEWARE STARTS")
        logging.info(f"middleware request.state: {dir(request.state)}")

        required_permissions = getattr(request.state, "required_permissions", None)
        logging.info(f"required_permissions: {required_permissions}")

        path = request.url.path
        if any(re.match(pattern, path) for pattern in self.public_routes):
            return await call_next(request)
        logging.info("is_public_route")
        
        logging.info("getting token")
        token = request.headers.get("Authorization", "").split("Bearer ")[-1]
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"}
            )

        try:

            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            user_id = UUID(payload.get("sub"))
            token_permissions = payload.get("permissions", [])
        except (JWTError, ValueError):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"}
            )


        success, msg, db_permissions = await self.user_service.get_user_permissions(user_id)
        if not success:
            return JSONResponse(
                status_code=404,
                content={"detail": msg}
            )
        all_permissions = list(set(token_permissions + db_permissions))
        request.state.permissions = all_permissions

        required_permission = self.get_required_permission(request)
        if required_permission not in all_permissions:
            return JSONResponse(
                status_code=403,
                content={"detail": "Permission denied"}
            )

        return await call_next(request)

    async def is_public_route(self, request: Request) -> bool:
        route = request.scope.get("route")
        logging.info(f"route: {route}")
        logging.info(f"route.path: {route.path}")
        return not route or route.path not in self.route_permissions

    def get_required_permission(self, request: Request) -> str:
        route = request.scope.get("route")
        if not route:
            return ""
        return self.route_permissions.get(get_request_handler(route).path, "")
    
    # def get_required_permission(self, request: Request) -> str:
    #     route_permissions = {
    #         "/roles/{role_id}": "role_read",
    #         "/movies": "movie_read",
    #     }
    #     return route_permissions.get(request.url.path, "")
    
    