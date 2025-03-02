from datetime import UTC, datetime

from src.services.auth_service import AuthService
from src.models.login import LoginResponse


class LoginService():
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def login_by_credentials_and_return_jwt_pair(
            self, username, password
    ) -> LoginResponse:
        """Authenticate user by credentials and return JWT pair."""
        user = await self.auth_service.authenticate_user(
            username=username, password=password)
        if not user:
            return None
        
        if not user.token_version:
            user.token_version = datetime.now(UTC)
            await self.auth_service.user_repository.update(user=user)

        access_jwt = self.auth_service.create_access_token(
            user_id=user.id, token_version=user.token_version)
        refresh_jwt = self.auth_service.create_refresh_token(
            user_id=user.id, token_version=user.token_version)

        return LoginResponse(
            access_token=access_jwt, refresh_token=refresh_jwt)
