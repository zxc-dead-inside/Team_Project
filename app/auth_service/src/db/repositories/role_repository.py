"""Repository for role management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.db.models import Permission, Role


class RoleRepository:
    """Repository for managing roles."""

    def __init__(self, session_factory):
        """Initialize the repository with a session factory."""
        self.session_factory = session_factory

    async def get_all(self) -> list[Role]:
        """Get all roles with their permissions."""
        async with self.session_factory() as session:
            stmt = (
                select(Role).options(joinedload(Role.permissions)).order_by(Role.name)
            )
            result = await session.execute(stmt)
            return list(result.scalars().unique())

    async def get_by_id(self, role_id: UUID) -> Role | None:
        """Get a role by ID."""
        async with self.session_factory() as session:
            stmt = (
                select(Role)
                .options(joinedload(Role.permissions))
                .where(Role.id == role_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_name(self, name: str) -> Role | None:
        """Get a role by name."""
        async with self.session_factory() as session:
            stmt = (
                select(Role)
                .options(joinedload(Role.permissions))
                .where(Role.name == name)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def create(
        self, name: str, description: str, permission_ids: list[UUID] | None = None
    ) -> Role:
        """Create a new role."""
        async with self.session_factory() as session:
            role = Role(name=name, description=description)
            session.add(role)

            # Add permissions if provided
            if permission_ids:
                # Get permissions
                permissions_stmt = select(Permission).where(
                    Permission.id.in_(permission_ids)
                )
                result = await session.execute(permissions_stmt)
                permissions = list(result.scalars())

                # Add permissions to role
                role.permissions = permissions

            await session.commit()

            stmt = (
                select(Role)
                .options(joinedload(Role.permissions))
                .where(Role.id == role.id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(
        self,
        role_id: UUID,
        name: str | None = None,
        description: str | None = None,
        permission_ids: list[UUID] | None = None,
    ) -> Role | None:
        """Update a role."""
        async with self.session_factory() as session:
            stmt = (
                select(Role)
                .options(joinedload(Role.permissions))
                .where(Role.id == role_id)
            )
            result = await session.execute(stmt)
            role = result.scalars().first()

            if not role:
                return None

            # Update fields if provided
            if name is not None:
                role.name = name
            if description is not None:
                role.description = description

            # Update permissions if provided
            if permission_ids is not None:
                permissions_stmt = select(Permission).where(
                    Permission.id.in_(permission_ids)
                )
                result = await session.execute(permissions_stmt)
                permissions = list(result.scalars())

                # Set new permissions
                role.permissions = permissions

            await session.commit()

            # Reload the role with permissions after updating
            stmt = (
                select(Role)
                .options(joinedload(Role.permissions))
                .where(Role.id == role.id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def delete(self, role_id: UUID) -> bool:
        """Delete a role."""
        async with self.session_factory() as session:
            stmt = select(Role).where(Role.id == role_id)
            result = await session.execute(stmt)
            role = result.scalars().first()

            if not role:
                return False

            await session.delete(role)
            await session.commit()
            return True
