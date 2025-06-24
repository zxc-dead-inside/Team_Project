"""Repository for audit log operations."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import AsyncContextManager
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.db.models.audit_log import AuditLog


class AuditLogRepository:
    """Repository for audit log operations."""

    def __init__(
        self, session_factory: Callable[[], AsyncContextManager[AsyncSession]]
    ):
        """
        Initialize the repository.

        Args:
            session_factory: Factory function that returns a session context manager
        """
        self.session_factory = session_factory

    async def create(self, audit_log: AuditLog) -> AuditLog:
        """
        Create a new audit log entry.

        Args:
            audit_log: AuditLog object

        Returns:
            AuditLog: Created audit log entry
        """
        async with self.session_factory() as session:
            session.add(audit_log)
            await session.flush()
            await session.refresh(audit_log)
            await session.commit()
            return audit_log

    async def log_action(
        self,
        action: str,
        actor_id: UUID | None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """
        Log an action in the audit log.

        Args:
            action: Action name
            actor_id: ID of the user who performed the action
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            details: Additional details about the action
            ip_address: IP address of the actor

        Returns:
            AuditLog: Created audit log entry
        """
        audit_log = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            timestamp=datetime.now(UTC),
        )
        return await self.create(audit_log)

    async def get_by_filters(
        self,
        page: int = 1,
        size: int = 20,
        actions: list[str] | None = None,
        actor_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        include_actor: bool = False,
    ) -> tuple[list[AuditLog], int]:
        """
        Get audit log entries with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            size: Page size
            actions: Optional list of actions to filter by
            actor_id: Optional actor ID to filter by
            resource_type: Optional resource type to filter by
            resource_id: Optional resource ID to filter by
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            include_actor: Whether to include the actor relationship

        Returns:
            tuple[list[AuditLog], int]: List of audit log entries and total count
        """
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)

        if include_actor:
            query = query.options(joinedload(AuditLog.actor))

        filters = []

        if actions:
            filters.append(AuditLog.action.in_(actions))

        if actor_id:
            filters.append(AuditLog.actor_id == actor_id)

        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)

        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)

        if start_date:
            filters.append(AuditLog.timestamp >= start_date)

        if end_date:
            filters.append(AuditLog.timestamp <= end_date)

        for filter_condition in filters:
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)

        query = query.order_by(AuditLog.timestamp.desc())

        query = query.offset((page - 1) * size).limit(size)

        async with self.session_factory() as session:
            result = await session.execute(query)
            count_result = await session.execute(count_query)

            items = result.scalars().all()
            total = count_result.scalar() or 0

            return items, total

    async def get_superuser_actions(
        self,
        page: int = 1,
        size: int = 20,
        include_actor: bool = True,
    ) -> tuple[list[AuditLog], int]:
        """
        Get audit log entries specifically for superuser-related actions.

        Args:
            page: Page number (1-indexed)
            size: Page size
            include_actor: Whether to include the actor relationship

        Returns:
            tuple[list[AuditLog], int]: List of audit log entries and total count
        """
        superuser_actions = [
            "grant_superuser",
            "revoke_superuser",
            "superuser_login",
            "superuser_action",
        ]

        return await self.get_by_filters(
            page=page,
            size=size,
            actions=superuser_actions,
            include_actor=include_actor,
        )
