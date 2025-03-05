"""Service for user-related operations."""

from datetime import datetime
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
        self.user_repository = user_repository
        self.login_history_repository = login_history_repository
        self.auth_service = auth_service

    async def get_user_profile(self, user_id: UUID) -> User | None:
        """
        Get user profile by ID.

        Args:
            user_id: User ID

        Returns:
            User | None: User if found, None otherwise
        """
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
