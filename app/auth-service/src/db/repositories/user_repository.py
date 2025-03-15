"""Repository for User model operations."""

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID
from src.db.models import Role
from src.db.models.user import User
from src.db.models.token_blacklist import TokenBlacklist
from src.db.models.login_history import LoginHistory


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session_factory):
        """Initialize the repository."""
        self.session_factory = session_factory

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Get a user by ID with roles and permissions.

        Args:
            user_id: User`s ID to find User

        Returns:
            Optional[User]: User found by user_id, None otherwise
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(User)
                .options(joinedload(User.roles).joinedload(Role.permissions))
                .where(User.id == user_id)
            )
            return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        """
        Get a user by username.

        Args:
            username: username to find User

        Returns:
            Optional[User]: User found by username, None otherwise
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )

            return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email.

        Args:
            email: email to find User

        Returns:
            Optional[User]: User found by email, None otherwise
        """
        async with self.session_factory() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalars().first()

    async def create(self, user: User) -> User:
        """
        Create a new user.

        Args:
            user: User to update

        Returns:
            User: Created User object
        """
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

    async def update_token_blacklist(self, token: TokenBlacklist):
        """
        Add refresh_token to blacklist.

        Args:
            token: RefreshToken

        Returns:
            None
        """
        async with self.session_factory() as session:
            session.add(token)
            await session.flush()
            await session.refresh(token)
            return None

    async def get_token_from_blacklist(self, token_jti: UUID) -> UUID | None:
        """
        Get token from blacklist by jti.

        Args:
            token_jti: Token`s jti

        Returns:
            Optional[UUID(token)]: Token`s jti if found, None otherwise
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(TokenBlacklist).filter(TokenBlacklist.jti == token_jti))
            return result.scalars().first()

    async def update(self, user: User) -> User:
        """
        Update an existing user.

        Args:
            user: User to update

        Returns:
            User: Updated User object
        """
        async with self.session_factory() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def assign_role(self, user_id: UUID, role_id: UUID) -> User | None:
        """
        Assign a role to a user.

        Args:
            user_id: The user ID
            role_id: The role ID to assign

        Returns:
            User | None: Updated user or None if user or role not found
        """
        async with self.session_factory() as session:
            stmt_user = (
                select(User).where(User.id == user_id).options(joinedload(User.roles))
            )
            result_user = await session.execute(stmt_user)
            user = result_user.scalars().first()

            if not user:
                return None

            stmt_role = select(Role).where(Role.id == role_id)
            result_role = await session.execute(stmt_role)
            role = result_role.scalars().first()

            if not role:
                return None

            if role.id in [r.id for r in user.roles]:
                return user

            user.roles.append(role)
            await session.commit()

            stmt_updated = (
                select(User).where(User.id == user_id).options(joinedload(User.roles))
            )
            result_updated = await session.execute(stmt_updated)
            return result_updated.scalars().first()

    async def remove_role(self, user_id: UUID, role_id: UUID) -> User | None:
        """
        Remove a role from a user.

        Args:
            user_id: The user ID
            role_id: The role ID to remove

        Returns:
            User | None: Updated user or None if user or role not found or user doesn't have the role
        """
        async with self.session_factory() as session:
            stmt_user = (
                select(User).where(User.id == user_id).options(joinedload(User.roles))
            )
            result_user = await session.execute(stmt_user)
            user = result_user.scalars().first()

            if not user:
                return None

            stmt_role = select(Role).where(Role.id == role_id)
            result_role = await session.execute(stmt_role)
            role = result_role.scalars().first()

            if not role:
                return None

            if role.id not in [r.id for r in user.roles]:
                return None

            user.roles = [r for r in user.roles if r.id != role.id]
            await session.commit()

            stmt_updated = (
                select(User).where(User.id == user_id).options(joinedload(User.roles))
            )
            result_updated = await session.execute(stmt_updated)
            return result_updated.scalars().first()

    async def bulk_assign_roles(
        self, user_id: UUID, role_ids: list[UUID]
    ) -> tuple[User | None, list[str]]:
        """
        Assign multiple roles to a user.

        Args:
            user_id: The user ID
            role_ids: List of role IDs to assign

        Returns:
            tuple[User | None, list[str]]: Updated user and list of added role names, or None if user not found
        """
        async with self.session_factory() as session:
            stmt_user = (
                select(User).where(User.id == user_id).options(joinedload(User.roles))
            )
            result_user = await session.execute(stmt_user)
            user = result_user.scalars().first()

            if not user:
                return None, []

            user_role_ids = [r.id for r in user.roles]

            added_role_names = []
            for role_id in role_ids:
                if role_id not in user_role_ids:
                    stmt_role = select(Role).where(Role.id == role_id)
                    result_role = await session.execute(stmt_role)
                    role = result_role.scalars().first()

                    if role:
                        user.roles.append(role)
                        added_role_names.append(role.name)

            if added_role_names:
                await session.commit()

            stmt_updated = (
                select(User).where(User.id == user_id).options(joinedload(User.roles))
            )
            result_updated = await session.execute(stmt_updated)
            return result_updated.scalars().first(), added_role_names

    async def get_user_with_roles(self, user_id: UUID) -> User | None:
        """
        Get a user by ID with their roles.

        Args:
            user_id: The user ID

        Returns:
            User | None: User with roles or None if not found
        """
        async with self.session_factory() as session:
            stmt = (
                select(User).where(User.id == user_id).options(joinedload(User.roles))
            )
            result = await session.execute(stmt)
            return result.scalars().first()
