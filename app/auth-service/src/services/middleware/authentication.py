from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.services.auth_service import AuthService

@inject
class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.public_routes = set()
    
    async def dispatch(self, request: Request, call_next):
        print('???????????')
        # Pass public requests
        if request.url.path in self.public_routes:
            response = await call_next(request)
            return response

        token: str = request.headers.get('Authorization', None)
        if not token:
            raise HTTPException(
                status_code=401, detail='Authorization token missing')

        if not self.auth_service.validate_token(token=token):
            raise HTTPException(status_code=401, detail='Invalid token')

        response = await call_next(request)
        return response

    def add_public_route(self, path: str):
        """
        Метод для добавления публичного маршрута в список.
        """
        self.public_routes.add(path)
