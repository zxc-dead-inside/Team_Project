"""Repository for login history."""

from collections.abc import Callable
from datetime import datetime
from typing import AsyncContextManager
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.login_history import LoginHistory


class LoginHistoryRepository:
    """Repository for login history operations."""

    def __init__(
        self, session_factory: Callable[[], AsyncContextManager[AsyncSession]]
    ):
        """
        Initialize the repository.

        Args:
            session_factory: Factory function that returns a session context manager
        """
        self.session_factory = session_factory

    async def create(self, login_history: LoginHistory) -> LoginHistory:
        """
        Create a new login history entry.

        Args:
            login_history: LoginHistory object

        Returns:
            LoginHistory: Created login history
        """
        async with self.session_factory() as session:
            session.add(login_history)
            await session.flush()
            await session.refresh(login_history)
            return login_history

    async def get_by_user_id(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        successful_only: bool | None = None,
    ) -> tuple[list[LoginHistory], int]:
        """
        Get login history entries for a user with pagination and filtering.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            size: Page size
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            successful_only: Optional filter for successful logins

        Returns:
            Tuple[List[LoginHistory], int]: List of login history entries and total count
        """
        # Base query
        query = select(LoginHistory).where(LoginHistory.user_id == user_id)
        count_query = (
            select(func.count())
            .select_from(LoginHistory)
            .where(LoginHistory.user_id == user_id)
        )

        # Apply filters
        if start_date:
            query = query.where(LoginHistory.login_time >= start_date)
            count_query = count_query.where(LoginHistory.login_time >= start_date)

        if end_date:
            query = query.where(LoginHistory.login_time <= end_date)
            count_query = count_query.where(LoginHistory.login_time <= end_date)

        if successful_only is not None:
            success_value = "Y" if successful_only else "N"
            query = query.where(LoginHistory.successful == success_value)
            count_query = count_query.where(LoginHistory.successful == success_value)

        # Apply ordering
        query = query.order_by(LoginHistory.login_time.desc())

        # Apply pagination
        query = query.offset((page - 1) * size).limit(size)

        # Execute queries
        async with self.session_factory() as session:
            result = await session.execute(query)
            count_result = await session.execute(count_query)

            items = list(result.scalars().all())
            total = count_result.scalar() or 0

            return items, total
