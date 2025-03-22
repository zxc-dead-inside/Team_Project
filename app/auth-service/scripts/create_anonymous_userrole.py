"""
Script to create the anonymous role and assign appropriate permissions.
This can be run independently to add anonymous user support to an existing system.
"""

import argparse
import asyncio
import logging
import os
import sys

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.schemas.permissions import PermissionCreate
from src.core.config import get_settings
from src.core.logger import setup_logging
from src.db.database import Database
from src.db.models import Permission, Role, role_permission


setup_logging()
settings = get_settings()
db_url = str(settings.database_url)

# Anonymous role constants
ANONYMOUS_ROLE_NAME = "anonymous"
ANONYMOUS_ROLE_DESCRIPTION = "Role for unauthenticated users with limited access"

# Anonymous permissions
ANONYMOUS_PERMISSIONS = [
    {"name": "view_public_content", "description": "Permission to view public content"},
    {
        "name": "access_public_endpoints",
        "description": "Permission to access public endpoints",
    },
    {
        "name": "read_public_resources",
        "description": "Permission to read public resources",
    },
]


async def create_permission(
    session: AsyncSession, name: str, description: str | None = None
) -> Permission | None:
    """
    Create a permission if it doesn't exist.

    Args:
        session: Database session
        name: Permission name
        description: Permission description

    Returns:
        Permission object or None if failed
    """
    try:
        # Validate permission data
        validated_data = PermissionCreate(name=name, description=description)

        # Check if permission exists
        result = await session.execute(
            select(Permission).filter(Permission.name == validated_data.name)
        )
        existing_permission = result.scalars().first()

        if existing_permission:
            logging.info(f"Permission '{validated_data.name}' already exists.")
            return existing_permission

        # Create new permission
        permission = Permission(
            name=validated_data.name,
            description=validated_data.description,
        )

        session.add(permission)
        await session.flush()

        logging.info(f"Created permission: {validated_data.name}")
        return permission

    except Exception as e:
        logging.error(f"Error creating permission '{name}': {e}")
        return None


async def create_anonymous_role_and_permissions(dry_run: bool = False) -> bool:
    """
    Create anonymous role and permissions.

    Args:
        dry_run: If True, just print what would be done without making changes

    Returns:
        bool: Success status
    """
    if dry_run:
        logging.info("DRY RUN: The following would be created:")
        logging.info(f"Role: {ANONYMOUS_ROLE_NAME} - {ANONYMOUS_ROLE_DESCRIPTION}")
        logging.info("Permissions:")
        for perm in ANONYMOUS_PERMISSIONS:
            logging.info(f"  - {perm['name']}: {perm['description']}")
        return True

    db = Database(db_url)

    async with db.session() as session:
        try:
            async with session.begin():
                # Check if role exists
                result = await session.execute(
                    select(Role).filter(Role.name == ANONYMOUS_ROLE_NAME)
                )
                existing_role = result.scalars().first()

                if existing_role:
                    logging.info(f"Role '{ANONYMOUS_ROLE_NAME}' already exists.")

                    # Delete existing role-permission associations for this role
                    query = delete(role_permission).where(
                        role_permission.c.role_id == existing_role.id
                    )
                    await session.execute(query)

                    anonymous_role = existing_role
                else:
                    anonymous_role = Role(
                        name=ANONYMOUS_ROLE_NAME,
                        description=ANONYMOUS_ROLE_DESCRIPTION,
                    )
                    session.add(anonymous_role)
                    await session.flush()
                    logging.info(f"Created role: {ANONYMOUS_ROLE_NAME}")

                # Get all permissions first
                permissions = []
                for perm_data in ANONYMOUS_PERMISSIONS:
                    permission = await create_permission(
                        session, perm_data["name"], perm_data["description"]
                    )
                    if permission:
                        permissions.append(permission)

                # Add all permissions to the role
                if permissions:
                    for permission in permissions:
                        # When role_id and permission_id are known, directly create the association
                        stmt = role_permission.insert().values(
                            role_id=anonymous_role.id, permission_id=permission.id
                        )
                        await session.execute(stmt)

                await session.flush()
                logging.info(
                    f"Assigned {len(permissions)} permissions to {ANONYMOUS_ROLE_NAME} role"
                )

            return True

        except Exception as e:
            logging.error(f"Error creating anonymous role: {e}")
            return False


async def main(args):
    """Main function to run script."""
    logging.info("Starting anonymous role creation...")

    success = await create_anonymous_role_and_permissions(args.dry_run)

    if args.dry_run:
        logging.info("DRY RUN: No changes were made to the database.")
    elif success:
        logging.info("Anonymous role and permissions created successfully!")
    else:
        logging.error("Failed to create anonymous role and permissions.")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create anonymous role and permissions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't make any changes, just print what would be done",
    )

    parsed_args = parser.parse_args()
    exit_code = asyncio.run(main(parsed_args))
    sys.exit(exit_code)
