"""Service for user-related operations."""

from datetime import UTC, datetime
from fastapi import Request
import logging
from uuid import UUID

from src.api.schemas.user_roles import UserRoleResponse
from src.core.logger import setup_logging
from src.db.models.login_history import LoginHistory
from src.db.models.user import User
from src.db.repositories.login_history_repository import LoginHistoryRepository
from src.db.repositories.role_repository import RoleRepository
from src.db.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.redis_service import RedisService


setup_logging()


class UserService:
    """Service for user-related operations."""

    def __init__(
        self,
        user_repository: UserRepository,
        login_history_repository: LoginHistoryRepository,
        auth_service: AuthService,
        redis_service: RedisService,
        role_repository: RoleRepository,
        user: User = None
    ):
        """Initialize the user service."""
        
        self.user_repository = user_repository
        self.login_history_repository = login_history_repository
        self.auth_service = auth_service
        self.redis_service = redis_service
        self.role_repository = role_repository
        self.user = user

        self.user_cache_key_prefix = "user:"
        self.user_roles_cache_key_prefix = "user_roles:"

    async def create_user(self, user: User) -> User:
        """Create a new user using UserRepository."""
        return await self.user_repository.create(user)

    async def _invalidate_user_cache(self, user_id: UUID):
        """Invalidate cache for a user and their roles."""
        try:
            user_key = f"{self.user_cache_key_prefix}{user_id}"
            await self.redis_service.delete(user_key)

            user_roles_key = f"{self.user_roles_cache_key_prefix}{user_id}"
            await self.redis_service.delete(user_roles_key)

            logging.debug(f"Cache invalidated for user {user_id}")
        except Exception as e:
            logging.error(f"Error invalidating user cache: {e}")

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
        
        if not user or user.is_active == False:
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
        
        jwt_pair = await self.auth_service.refresh_tokens_for_user(user=user)

        await self.auth_service.user_repository.update(user=user)

        await self.auth_service.user_repository.update_history(
            login_history=login_history)

        return jwt_pair

    async def logout_from_all_device(self) -> tuple[str, str]:
        """
        Logout from all device and return new JWT pair with new token_version.

        Returns:
            tuple[str, str]: (access_token, refresh_jwt)
        """

        self.user.token_version = datetime.now(UTC)
        jwt_pair = await self.auth_service.refresh_tokens_for_user(user=self.user)
        
        await self.auth_service.user_repository.update(user=self.user)

        return jwt_pair
    
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
        
        jwt_pair = await self.auth_service.refresh_tokens_for_user(user=self.user)

        await self.auth_service.update_token_blacklist(
            refresh_token
        )
        return jwt_pair

    async def assign_role_to_user(
        self, user_id: UUID, role_id: UUID
    ) -> tuple[bool, str, User | None]:
        """
        Assign a role to a user.

        Args:
            user_id: The user ID
            role_id: The role ID to assign

        Returns:
            tuple[bool, str, User | None]: (success, message, updated user)
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False, f"User with ID {user_id} not found", None

        role = await self.role_repository.get_by_id(role_id)
        if not role:
            return False, f"Role with ID {role_id} not found", None

        updated_user = await self.user_repository.assign_role(user_id, role_id)

        if not updated_user:
            return False, "Failed to assign role to user", None

        if role_id in [r.id for r in user.roles]:
            return False, f"User already has role '{role.name}'", user

        await self._invalidate_user_cache(user_id)

        return True, f"Role '{role.name}' assigned to user", updated_user

    async def remove_role_from_user(
        self, user_id: UUID, role_id: UUID
    ) -> tuple[bool, str, User | None]:
        """
        Remove a role from a user.

        Args:
            user_id: The user ID
            role_id: The role ID to remove

        Returns:
            tuple[bool, str, User | None]: (success, message, updated user)
        """
        user = await self.user_repository.get_user_with_roles(user_id)
        if not user:
            return False, f"User with ID {user_id} not found", None

        role = await self.role_repository.get_by_id(role_id)
        if not role:
            return False, f"Role with ID {role_id} not found", None

        if role_id not in [r.id for r in user.roles]:
            return False, f"User does not have role '{role.name}'", user

        if len(user.roles) == 1:
            return False, "Cannot remove the last role from a user", user

        updated_user = await self.user_repository.remove_role(user_id, role_id)

        if not updated_user:
            return False, "Failed to remove role from user", None

        await self._invalidate_user_cache(user_id)

        return True, f"Role '{role.name}' removed from user", updated_user

    async def bulk_assign_roles(
        self, user_id: UUID, role_ids: list[UUID]
    ) -> tuple[bool, str, User | None]:
        """
        Assign multiple roles to a user.

        Args:
            user_id: The user ID
            role_ids: List of role IDs to assign

        Returns:
            tuple[bool, str, User | None]: (success, message, updated user)
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False, f"User with ID {user_id} not found", None

        for role_id in role_ids:
            role = await self.role_repository.get_by_id(role_id)
            if not role:
                return False, f"Role with ID {role_id} not found", None

        updated_user, added_roles = await self.user_repository.bulk_assign_roles(
            user_id, role_ids
        )

        if not updated_user:
            return False, "Failed to assign roles to user", None

        if not added_roles:
            return False, "No new roles to assign", user

        await self._invalidate_user_cache(user_id)

        return (
            True,
            f"Roles assigned to user: {', '.join(added_roles)}",
            updated_user,
        )

    async def get_user_roles(
        self, user_id: UUID
    ) -> tuple[bool, str, UserRoleResponse | None]:
        """
        Get all roles assigned to a user with caching.

        Args:
            user_id: The user ID

        Returns:
            tuple[bool, str, UserRoleResponse | None]: (success, message, response)
        """
        user_roles_key = f"{self.user_roles_cache_key_prefix}{user_id}"
        cached_roles = await self.redis_service.get_model(
            user_roles_key, UserRoleResponse
        )
        if cached_roles:
            logging.debug(f"Returning user roles for {user_id} from cache")
            return True, "User roles retrieved from cache", cached_roles

        user = await self.user_repository.get_user_with_roles(user_id)
        if not user:
            return False, f"User with ID {user_id} not found", None

        response = UserRoleResponse(
            user_id=user_id,
            role_ids=[role.id for role in user.roles],
            role_names=[role.name for role in user.roles],
        )

        await self.redis_service.set_model(user_roles_key, response)
        logging.debug(f"Cached user roles for {user_id}")

        return True, "User roles retrieved successfully", response
