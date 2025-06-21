"""
Seed script to create initial data for the application.
"""

import asyncio
import logging
import os
import sys
import uuid

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.config import get_settings
from src.db.database import Database
from src.db.models import ContentRestriction, Permission, Role, User


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
db_url = str(settings.database_url)

# Set up password context
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


async def create_roles(session: AsyncSession) -> dict:
    """Create initial roles."""
    logger.info("Creating roles...")

    roles = {
        "admin": Role(name="admin", description="Administrator with full access"),
        "moderator": Role(name="moderator", description="Content moderator"),
        "subscriber": Role(name="subscriber", description="Paid subscriber"),
        "user": Role(name="user", description="Regular user"),
        "anonymous": Role(
            name="anonymous",
            description="Role for unauthenticated users with limited access"
        ),
    }

    for role in roles.values():
        session.add(role)

    await session.flush()
    logger.info(f"Created {len(roles)} roles")
    return roles


async def create_permissions(session: AsyncSession) -> dict:
    """Create initial permissions."""
    logger.info("Creating permissions...")

    permissions = {
        "user_create": Permission(name="user_create",
                                  description="Create users"),
        "user_read": Permission(name="user_read",
                                description="Read user details"),
        "user_update": Permission(name="user_update",
                                  description="Update users"),
        "user_delete": Permission(name="user_delete",
                                  description="Delete users"),
        "role_create": Permission(name="role_create",
                                  description="Create roles"),
        "role_read": Permission(name="role_read",
                                description="Read roles"),
        "role_update": Permission(name="role_update",
                                  description="Update roles"),
        "role_delete": Permission(name="role_delete",
                                  description="Delete roles"),
        "content_all": Permission(name="content_all",
                                  description="Access all content"),
        "content_recent": Permission(name="content_recent",
                                     description="Access recent content"),
        "view_public_content": Permission(
            name="view_public_content",
            description="Permission to view public content"
        ),
        "access_public_endpoints": Permission(
            name="access_public_endpoints",
            description="Permission to access public endpoints"
        ),
        "read_public_resources": Permission(
            name="read_public_resources",
            description="Permission to read public resources"
        ),

    }

    for permission in permissions.values():
        session.add(permission)

    await session.flush()
    logger.info(f"Created {len(permissions)} permissions")
    return permissions


async def assign_permissions_to_roles(
    session: AsyncSession, roles: dict, permissions: dict
) -> None:
    """Assign permissions to roles without triggering lazy loading."""
    logger.info("Assigning permissions to roles...")

    # Use set_committed_value to assign without triggering lazy load.
    set_committed_value(roles["admin"], "permissions", list(permissions.values()))
    await session.flush()

    set_committed_value(
        roles["moderator"],
        "permissions",
        [
            permissions["user_read"],
            permissions["role_read"],
            permissions["content_all"],
        ],
    )
    await session.flush()

    set_committed_value(
        roles["subscriber"],
        "permissions",
        [
            permissions["content_all"],
            permissions["content_recent"],
        ],
    )
    await session.flush()

    set_committed_value(roles["user"], "permissions", [permissions["content_recent"]])
    await session.flush()

    set_committed_value(
        roles["anonymous"],
        "permissions",
        [
            permissions["view_public_content"],
            permissions["access_public_endpoints"],
            permissions["read_public_resources"],
        ],
    )
    await session.flush()

    logger.info("Permissions assigned to roles")


async def create_superuser(session: AsyncSession, roles: dict) -> None:
    """Create a superuser account."""
    logger.info("Creating superuser...")

    superuser = User(
        username="admin",
        email="admin@example.com",
        password=pwd_context.hash("admin"),
        is_active=True,
        is_superuser=True,
    )

    superuser.roles.append(roles["admin"])
    session.add(superuser)

    await session.flush()
    logger.info("Superuser created")


async def create_content_restrictions(session: AsyncSession, roles: dict) -> None:
    """Create content restrictions."""
    logger.info("Creating content restrictions...")

    restrictions = [
        ContentRestriction(
            name="recent_movies",
            description="Movies released within the last 3 years",
            required_role_id=roles["subscriber"].id,
        ),
        ContentRestriction(
            name="premium_content",
            description="Premium content for subscribers only",
            required_role_id=roles["subscriber"].id,
        ),
    ]

    for restriction in restrictions:
        session.add(restriction)

    await session.flush()
    logger.info(f"Created {len(restrictions)} content restrictions")


async def main():
    """Main function to run seed script."""
    logger.info("Starting seed script...")

    db = Database(db_url)

    async with db.session() as session:
        try:
            # Create initial data
            roles = await create_roles(session)
            permissions = await create_permissions(session)
            await assign_permissions_to_roles(session, roles, permissions)
            await create_superuser(session, roles)
            await create_content_restrictions(session, roles)

            logger.info("Seed completed successfully!")

        except Exception as e:
            logger.error(f"Error in seed script: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
