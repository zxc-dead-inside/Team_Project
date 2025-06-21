"""Service for role management with Redis caching."""

import logging
from uuid import UUID

from pydantic import TypeAdapter
from src.api.schemas.roles import RoleCreate, RoleResponse, RoleUpdate
from src.core.logger import setup_logging
from src.db.models.role import Role
from src.db.repositories.role_repository import RoleRepository
from src.services.redis_service import RedisService


setup_logging()


class RoleService:
    """Service for managing roles with Redis caching."""

    def __init__(
        self,
        role_repository: RoleRepository,
        redis_service: RedisService,
    ):
        """Initialize the role service.

        Args:
            role_repository: Repository for role operations
            redis_service: Service for Redis caching
        """
        self.role_repository = role_repository
        self.redis_service = redis_service

        # Define cache keys
        self.all_roles_cache_key = "roles:all"
        self.role_cache_key_prefix = "role:"

    async def _invalidate_cache(self, role_id: UUID | None = None):
        """Invalidate cache for roles.

        Args:
            role_id: If provided, only invalidate this specific role
        """
        try:
            # Always invalidate the all_roles cache
            await self.redis_service.delete(self.all_roles_cache_key)

            # If role_id is provided, also invalidate that specific role
            if role_id:
                role_key = f"{self.role_cache_key_prefix}{role_id}"
                await self.redis_service.delete(role_key)

            logging.debug(f"Cache invalidated for roles (role_id={role_id})")
        except Exception as e:
            logging.error(f"Error invalidating role cache: {e}")

    async def get_all_roles(self) -> list[RoleResponse]:
        """Get all roles with caching."""
        # Try to get from cache first
        cached_roles = await self.redis_service.get_list(
            self.all_roles_cache_key, RoleResponse
        )
        if cached_roles:
            logging.debug("Returning roles from cache")
            return cached_roles

        # If not in cache or error, get from database
        roles = await self.role_repository.get_all()

        # Convert to response models
        role_adapter = TypeAdapter(list[RoleResponse])
        role_responses = role_adapter.validate_python([role for role in roles])

        # Cache the results
        await self.redis_service.set_list(self.all_roles_cache_key, role_responses)
        logging.debug("Cached all roles")

        return role_responses

    async def get_role_by_id(self, role_id: UUID) -> RoleResponse | None:
        """Get a role by ID with caching."""
        # Try to get from cache first
        role_key = f"{self.role_cache_key_prefix}{role_id}"
        cached_role = await self.redis_service.get_model(role_key, RoleResponse)
        if cached_role:
            logging.debug(f"Returning role {role_id} from cache")
            return cached_role

        # If not in cache or error, get from database
        role = await self.role_repository.get_by_id(role_id)
        if not role:
            return None

        # Convert to response model
        role_response = RoleResponse.model_validate(role)

        # Cache the result
        await self.redis_service.set_model(role_key, role_response)
        logging.debug(f"Cached role {role_id}")

        return role_response

    async def create_role(
        self, role_data: RoleCreate
    ) -> tuple[bool, str, RoleResponse | None]:
        """Create a new role.

        Args:
            role_data: Data for the new role

        Returns:
            Tuple containing:
                - Success flag
                - Message
                - Created role (if successful)
        """
        # Check if role with same name already exists
        existing_role = await self.role_repository.get_by_name(role_data.name)
        if existing_role:
            return False, f"Role with name '{role_data.name}' already exists", None

        try:
            # Create the role
            role = await self.role_repository.create(
                name=role_data.name,
                description=role_data.description,
                permission_ids=role_data.permission_ids,
            )

            # Invalidate cache
            await self._invalidate_cache()

            # Convert to response model
            role_response = RoleResponse.model_validate(role)
            return True, "Role created successfully", role_response

        except Exception as e:
            logging.error(f"Error creating role: {e}")
            return False, f"Failed to create role: {str(e)}", None

    async def update_role(
        self, role_id: UUID, role_data: RoleUpdate
    ) -> tuple[bool, str, RoleResponse | None]:
        """Update a role.

        Args:
            role_id: ID of the role to update
            role_data: Data to update

        Returns:
            Tuple containing:
                - Success flag
                - Message
                - Updated role (if successful)
        """
        # Check if role exists
        existing_role = await self.role_repository.get_by_id(role_id)
        if not existing_role:
            return False, f"Role with ID {role_id} not found", None

        # If name is being updated, check if it's unique
        if role_data.name is not None and role_data.name != existing_role.name:
            role_with_same_name = await self.role_repository.get_by_name(role_data.name)
            if role_with_same_name:
                return False, f"Role with name '{role_data.name}' already exists", None

        try:
            # Update the role
            updated_role = await self.role_repository.update(
                role_id=role_id,
                name=role_data.name,
                description=role_data.description,
                permission_ids=role_data.permission_ids,
            )

            # Invalidate cache
            await self._invalidate_cache(role_id)

            # Convert to response model
            role_response = RoleResponse.model_validate(updated_role)
            return True, "Role updated successfully", role_response

        except Exception as e:
            logging.error(f"Error updating role {role_id}: {e}")
            return False, f"Failed to update role: {str(e)}", None

    async def delete_role(self, role_id: UUID) -> tuple[bool, str]:
        """Delete a role.

        Args:
            role_id: ID of the role to delete

        Returns:
            Tuple containing:
                - Success flag
                - Message
        """
        # Check if role exists
        existing_role = await self.role_repository.get_by_id(role_id)
        if not existing_role:
            return False, f"Role with ID {role_id} not found"

        # Prevent deletion of system roles
        if existing_role.name in ["admin", "user"]:
            return False, f"Cannot delete system role '{existing_role.name}'"

        try:
            # Delete the role
            success = await self.role_repository.delete(role_id)
            if not success:
                return False, "Failed to delete role"

            # Invalidate cache
            await self._invalidate_cache(role_id)

            return True, "Role deleted successfully"

        except Exception as e:
            logging.error(f"Error deleting role {role_id}: {e}")
            return False, f"Failed to delete role: {str(e)}"

    async def get_role_by_name(self, name: str) -> Role | None:
        """Get a role by name (returns ORM model, not Pydantic schema)."""
        return await self.role_repository.get_by_name(name)


