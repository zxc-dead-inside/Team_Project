"""Repository for User model operations."""

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.db.models import Role
from src.db.models.user import User
from src.db.models.token_blacklist import TokenBlacklist
from src.db.models.login_history import LoginHistory


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session_factory):
        """Initialize the repository."""
        self.session_factory = session_factory

    async def get_by_id(self, user_id: int) -> User | None:
        """Get a user by ID with roles and permissions."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(User)
                .options(joinedload(User.roles).joinedload(Role.permissions))
                .where(User.id == user_id)
            )
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

    async def update_history(self, login_history: LoginHistory) -> None:
        """
        Update a user logins history.

        Args:
            user: LoginHistory to update

        Returns:
            None
        """
        async with self.session_factory() as session:
            session.add(login_history)
            await session.flush()
            await session.refresh(login_history)
            return None

    async def update_token_blacklist(self, token_blacklist):
        """
        Add refresh_token to blacklist.

        Args:
            token: RefreshToken

        Returns:
            None
        """
        async with self.session_factory() as session:
            session.add(token_blacklist)
            await session.flush()
            await session.refresh(token_blacklist)
            return None

    async def get_token_from_blacklist(self, token_jti):
        """
        Get token from blacklist.

        Args:
            token: Token`s jti

        Returns:
            Optional[str(token_jti)]: Token`s jti if found, None otherwise
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(TokenBlacklist).filter(TokenBlacklist.jti == token_jti))
            return result.scalars().first()

    async def update(self, user: User) -> User:
        """Update an existing user."""
        async with self.session_factory() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
