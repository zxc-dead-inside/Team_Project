"""Repository for User model operations."""

from sqlalchemy import select
from src.db.models.user import User


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session_factory):
        """Initialize the repository."""
        self.session_factory = session_factory

    async def get_by_id(self, user_id: int) -> User | None:
        """Get a user by ID."""
        async with self.session_factory() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        async with self.session_factory() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalars().first()

    async def create(self, user: User) -> User:
        """Create a new user."""
        async with self.session_factory() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def update(self, user: User) -> User:
        """Update an existing user."""
        async with self.session_factory() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
