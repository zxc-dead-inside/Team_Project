"""Service for managing superuser operations."""

import logging
from uuid import UUID

from src.db.models.user import User
from src.db.repositories.audit_log_repository import AuditLogRepository
from src.db.repositories.user_repository import UserRepository


logger = logging.getLogger(__name__)


class SuperuserService:
    """Service for managing superuser operations."""

    def __init__(
        self, user_repository: UserRepository, audit_log_repository: AuditLogRepository
    ):
        """
        Initialize the superuser service.

        Args:
            user_repository: User repository
            audit_log_repository: Audit log repository
        """
        self.user_repository = user_repository
        self.audit_log_repository = audit_log_repository

    async def list_superusers(self) -> list[User]:
        """
        List all superusers in the system.

        Returns:
            List of superuser objects
        """
        return await self.user_repository.get_all_superusers()

    async def grant_superuser(
        self, user_id: UUID, granted_by: UUID, ip_address: str | None = None
    ) -> tuple[bool, str, User | None]:
        """
        Grant superuser privileges to a user.

        Args:
            user_id: ID of the user to grant superuser privileges to
            granted_by: ID of the user granting superuser privileges
            ip_address: IP address of the user performing the action

        Returns:
            Tuple containing success status, message, and user object if successful
        """
        # Get the user to grant privileges to
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False, f"User with ID {user_id} not found", None

        # Get the user who is granting privileges
        granting_user = await self.user_repository.get_by_id(granted_by)
        if not granting_user:
            return False, f"Granting user with ID {granted_by} not found", None

        # Check if the granting user is a superuser
        if not granting_user.is_superuser:
            return False, "Only superusers can grant superuser privileges", None

        # Check if the user is already a superuser
        if user.is_superuser:
            return False, f"User {user.username} is already a superuser", None

        # Grant superuser privileges
        user.is_superuser = True
        updated_user = await self.user_repository.update(user)

        # Log the action
        await self.audit_log_repository.log_action(
            action="grant_superuser",
            actor_id=granted_by,
            resource_type="user",
            resource_id=user_id,
            ip_address=ip_address,
            details={
                "username": user.username,
                "email": user.email,
                "granted_by": granting_user.username,
            },
        )

        logger.warning(
            f"Superuser privileges granted to {user.username} by {granting_user.username}"
        )

        return True, f"Superuser privileges granted to {user.username}", updated_user

    async def revoke_superuser(
        self, user_id: UUID, revoked_by: UUID, ip_address: str | None = None
    ) -> tuple[bool, str, User | None]:
        """
        Revoke superuser privileges from a user.

        Args:
            user_id: ID of the user to revoke superuser privileges from
            revoked_by: ID of the user revoking superuser privileges
            ip_address: IP address of the user performing the action

        Returns:
            Tuple containing success status, message, and user object if successful
        """
        # Get the user to revoke privileges from
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False, f"User with ID {user_id} not found", None

        # Get the user who is revoking privileges
        revoking_user = await self.user_repository.get_by_id(revoked_by)
        if not revoking_user:
            return False, f"Revoking user with ID {revoked_by} not found", None

        # Check if the revoking user is a superuser
        if not revoking_user.is_superuser:
            return False, "Only superusers can revoke superuser privileges", None

        # Check if the user is a superuser
        if not user.is_superuser:
            return False, f"User {user.username} is not a superuser", None

        # Prevent revoking the last superuser
        superuser_count = await self.user_repository.count_superusers()
        if superuser_count <= 1 and user.is_superuser:
            return False, "Cannot revoke privileges from the last superuser", None

        # Revoke superuser privileges
        user.is_superuser = False
        updated_user = await self.user_repository.update(user)

        # Log the action
        await self.audit_log_repository.log_action(
            action="revoke_superuser",
            actor_id=revoked_by,
            resource_type="user",
            resource_id=user_id,
            ip_address=ip_address,
            details={
                "username": user.username,
                "email": user.email,
                "revoked_by": revoking_user.username,
            },
        )

        logger.warning(
            f"Superuser privileges revoked from {user.username} by {revoking_user.username}"
        )

        return True, f"Superuser privileges revoked from {user.username}", updated_user

    async def get_superuser_audit_log(
        self, page: int = 1, size: int = 20
    ) -> tuple[list[dict], int]:
        """
        Get audit log entries for superuser actions.

        Args:
            page: Page number (1-indexed)
            size: Page size

        Returns:
            Tuple containing list of audit log entries and total count
        """
        logs, total = await self.audit_log_repository.get_superuser_actions(
            page=page, size=size, include_actor=True
        )

        # Format the log entries
        formatted_logs = []
        for log in logs:
            actor_username = log.actor.username if log.actor else "Unknown"

            formatted_logs.append(
                {
                    "id": str(log.id),
                    "action": log.action,
                    "actor_id": str(log.actor_id) if log.actor_id else None,
                    "actor_username": actor_username,
                    "resource_type": log.resource_type,
                    "resource_id": str(log.resource_id) if log.resource_id else None,
                    "timestamp": log.timestamp.isoformat(),
                    "ip_address": log.ip_address,
                    "details": log.details or {},
                }
            )

        return formatted_logs, total
