from datetime import UTC, datetime
from fastapi import Request
import jwt

from src.db.models.user import User
from src.db.models.token_blacklist import TokenBlacklist
from src.db.models.login_history import LoginHistory
from src.models.login import LoginResponse
from src.services.auth_service import AuthService



class UserService:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.user: User
    
    async def login_by_credentials(
            self, username, password, request: Request
    ) -> LoginResponse:
        """Authenticate user by credentials and return JWT pair."""
        
        user: User = await self.auth_service.identificate_user(
            username=username)
        
        if not user:
            return None
        
        login_history = LoginHistory(
            user_id = user.id,
            user_agent = request.headers.get('User-Agent', None),
            ip_address = request.client.host,
            login_time = datetime.now(UTC),
            successful = 'Y'
        )

        if not await self.auth_service.authenticate_user(
            user=user, password=password):
            login_history.successful = 'N'
            await self.auth_service.user_repository.update_history(
                login_history=login_history)
            return None

        if user.token_version == None:
            user.token_version = datetime.now(UTC)
        await self.auth_service.user_repository.update(user=user)

        access_jwt = self.auth_service.create_access_token(
            user_id=user.id, token_version=user.token_version)
        refresh_jwt = self.auth_service.create_refresh_token(
            user_id=user.id, token_version=user.token_version)

        await self.auth_service.user_repository.update(user=user)

        await self.auth_service.user_repository.update_history(
            login_history=login_history)

        return LoginResponse(
            access_token=access_jwt, refresh_token=refresh_jwt)

    async def logout_from_all_device(self):
        self.user.token_version = datetime.now(UTC)
        await self.auth_service.user_repository.update(user=self.user)

        access_jwt = self.auth_service.create_access_token(
            user_id=self.user.id, token_version=self.user.token_version)
        refresh_jwt = self.auth_service.create_refresh_token(
            user_id=self.user.id, token_version=self.user.token_version)

        return LoginResponse(
            access_token=access_jwt, refresh_token=refresh_jwt)
    
    async def refresh_token(self, refresh_token):


        self.user = await self.auth_service.validate_token(
            token=refresh_token, type='refresh')
        
        await self.auth_service.check_refresh_token_blacklist(
            token=refresh_token)
        
        access_jwt = self.auth_service.create_access_token(
            user_id=self.user.id, token_version=self.user.token_version)
        refresh_jwt = self.auth_service.create_refresh_token(
            user_id=self.user.id, token_version=self.user.token_version)
        
        await self.auth_service.update_token_blacklist(
            refresh_token
        )

        return LoginResponse(
            access_token=access_jwt, refresh_token=refresh_jwt)