"""User repository for database operations."""

from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.user import User


class UserRepository:
    """Repository for user operations."""

    def __init__(
        self, session_factory: Callable[[], AbstractAsyncContextManager[AsyncSession]]
    ):
        """Initialize with the session factory."""
        self.session_factory = session_factory

    async def create(self, user: User) -> User:
        """
        Create a new user.

        Args:
            user: User to create

        Returns:
            User: Created user with ID
        """
        async with self.session_factory() as session:
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

    async def get_by_id(self, user_id: int) -> User | None:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            Optional[User]: User if found, None otherwise
        """
        async with self.session_factory() as session:
            result = await session.execute(select(User).filter(User.id == user_id))
            return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """
        Get a user by email.

        Args:
            email: User email

        Returns:
            Optional[User]: User if found, None otherwise
        """
        async with self.session_factory() as session:
            result = await session.execute(select(User).filter(User.email == email))
            return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        """
        Get a user by username.

        Args:
            username: Username

        Returns:
            Optional[User]: User if found, None otherwise
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(User).filter(User.username == username)
            )
            return result.scalars().first()

    async def update(self, user: User) -> User:
        """
        Update a user.

        Args:
            user: User to update

        Returns:
            User: Updated user
        """
        async with self.session_factory() as session:
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user
