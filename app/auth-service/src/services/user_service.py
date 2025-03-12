"""Service for user-related operations."""

from datetime import UTC, datetime
from fastapi import Request
from uuid import UUID

from src.db.models.login_history import LoginHistory
from src.db.models.user import User
from src.db.repositories.login_history_repository import LoginHistoryRepository
from src.db.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService


class UserService:
    """Service for user-related operations."""

    def __init__(
        self,
        user_repository: UserRepository,
        login_history_repository: LoginHistoryRepository,
        auth_service: AuthService,
    ):
        """Initialize the user service."""
        self.user_repository: UserRepository = user_repository
        self.login_history_repository: LoginHistoryRepository = login_history_repository
        self.auth_service: AuthService = auth_service
        self.user: User

    async def get_user_profile(self, user_id: UUID) -> User | None:
        """
        Get user profile by ID.

        Args:
            user_id: User ID

        Returns:
            User | None: User if found, None otherwise
        """
        if self.user.id == user_id: return self.user
        return await self.user_repository.get_by_id(user_id)

    async def update_username(
        self, user_id: UUID, new_username: str
    ) -> tuple[bool, str, User | None]:
        """
        Update a user's username.

        Args:
            user_id: User ID
            new_username: New username

        Returns:
            tuple[bool, str, User | None]: (success, message, updated user)
        """
        # Check if user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False, "User not found", None

        # Check if username is already taken
        existing_user = await self.user_repository.get_by_username(new_username)
        if existing_user and existing_user.id != user_id:
            return False, "Username already exists", None

        # Update username
        user.username = new_username
        updated_user = await self.user_repository.update(user)

        return True, "Username updated successfully", updated_user

    async def update_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> tuple[bool, str]:
        """
        Update a user's password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            tuple[bool, str]: (success, message)
        """
        # Check if user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False, "User not found"

        # Verify current password
        if not self.auth_service.verify_password(current_password, user.password):
            return False, "Current password is incorrect"

        # Hash new password
        hashed_password = self.auth_service.hash_password(new_password)

        # Update password
        user.password = hashed_password
        await self.user_repository.update(user)

        return True, "Password updated successfully"

    async def get_login_history(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        successful_only: bool | None = None,
    ) -> tuple[list[LoginHistory], int]:
        """
        Get login history for a user with pagination and filtering.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            size: Page size
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            successful_only: Optional filter for successful logins

        Returns:
            tuple[list[LoginHistory], int]: List of login history entries and total count
        """
        return await self.login_history_repository.get_by_user_id(
            user_id=user_id,
            page=page,
            size=size,
            start_date=start_date,
            end_date=end_date,
            successful_only=successful_only,
        )
    
    async def login_by_credentials(
            self, username: str, password: str, request: Request
    ) -> tuple[str, str] | None:
        """
        Authenticate user by credentials and return JWT pair.
        Creates event in LoginHistory.

        Args:
            username: User`s username
            password: User`s password

        Returns:
            tuple[str, str | None]: (access_token, refresh_jwt), None if Login failed
        """
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

        # Check token_version for multi-device-logout
        if user.token_version == None:
            user.token_version = datetime.now(UTC)

        access_token = self.auth_service.create_access_token(
            user_id=user.id, token_version=user.token_version)
        refresh_token = self.auth_service.create_refresh_token(
            user_id=user.id, token_version=user.token_version)

        await self.auth_service.user_repository.update(user=user)

        await self.auth_service.user_repository.update_history(
            login_history=login_history)

        return access_token, refresh_token

    async def logout_from_all_device(self) -> tuple[str, str]:
        """
        Logout from all device and return new JWT pair with new token_version.

        Returns:
            tuple[str, str]: (access_token, refresh_jwt)
        """

        self.user.token_version = datetime.now(UTC)
        
        access_token = self.auth_service.create_access_token(
            user_id=self.user.id, token_version=self.user.token_version)
        refresh_token = self.auth_service.create_refresh_token(
            user_id=self.user.id, token_version=self.user.token_version)
        
        await self.auth_service.user_repository.update(user=self.user)

        return access_token, refresh_token
    
    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """
        Validate refresh token and create new JWT pair.
        Adds current refresh token to blacklist.

        Returns:
            tuple[str, str] | None: (access_token, refresh_jwt)
        """
        self.user = await self.auth_service.validate_token(
            token=refresh_token, type='refresh')
        await self.auth_service.check_refresh_token_blacklist(
            token=refresh_token)

        access_token = self.auth_service.create_access_token(
            user_id=self.user.id, token_version=self.user.token_version)
        refresh_token = self.auth_service.create_refresh_token(
            user_id=self.user.id, token_version=self.user.token_version)
        
        await self.auth_service.update_token_blacklist(
            refresh_token
        )
        return access_token, refresh_token
