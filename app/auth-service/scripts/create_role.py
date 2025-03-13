import argparse
import asyncio
import logging
import os
import re
import sys

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select


# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.core.logger import setup_logging
from src.db.database import Database
from src.db.models import Permission, Role


# Configure logging
setup_logging()
settings = get_settings()
db_url = str(settings.database_url)


# Validator schema
class RoleCreate(BaseModel):
    """Validation schema for role creation."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)

    @field_validator("name")
    def name_format(cls, v):
        """Validate role name format."""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Role name must contain only letters, numbers, and underscores"
            )
        return v


async def list_all_permissions() -> None:
    """
    List all available permissions in the system.
    """
    db = Database(db_url)

    async with db.session() as session:
        result = await session.execute(select(Permission).order_by(Permission.name))
        permissions = result.scalars().all()

        if not permissions:
            logging.info("No permissions found in the system.")
            return

        logging.info("\nAvailable permissions:")
        logging.info("-" * 80)
        logging.info(f"{'NAME':<30} {'DESCRIPTION':<50}")
        logging.info("-" * 80)

        for permission in permissions:
            description = permission.description or ""
            logging.info(f"{permission.name:<30} {description:<50}")

        logging.info("")


async def get_permissions(session, permission_names: list[str]) -> list[Permission]:
    """
    Get permission objects by name.

    Args:
        session: Database session
        permission_names: List of permission names

    Returns:
        List of permission objects
    """
    if not permission_names:
        return []

    result = await session.execute(
        select(Permission).filter(Permission.name.in_(permission_names))
    )

    permissions = result.scalars().all()
    found_names = [p.name for p in permissions]

    missing = [name for name in permission_names if name not in found_names]
    if missing:
        logging.warning(
            f"The following permissions were not found: {', '.join(missing)}"
        )
        logging.warning("Use --list-permissions to see all available permissions.")

    return permissions


async def create_role(
    name: str,
    description: str | None = None,
    permissions: list[str] | None = None,
) -> bool:
    """
    Create a role with optional permissions.

    Args:
        name: Role name
        description: Role description
        permissions: List of permission names to assign

    Returns:
        True if role was created successfully, False otherwise
    """
    try:
        validated_data = RoleCreate(name=name, description=description)
    except Exception as e:
        logging.error(f"Validation error: {e}")
        return False

    logging.info(f"Creating role: {validated_data.name}")
    if validated_data.description:
        logging.info(f"Description: {validated_data.description}")

    db = Database(db_url)

    async with db.session() as session:
        try:
            result = await session.execute(
                select(Role).filter(Role.name == validated_data.name)
            )
            existing_role = result.scalars().first()

            if existing_role:
                logging.error(f"Role with name '{validated_data.name}' already exists.")
                return False

            role = Role(
                name=validated_data.name,
                description=validated_data.description,
            )

            if permissions:
                perm_objects = await get_permissions(session, permissions)
                role.permissions = (
                    perm_objects  # Replace with assignment instead of append
                )

            session.add(role)
            await session.commit()

            logging.info(f"Role '{validated_data.name}' created successfully!")

            if permissions and perm_objects:
                logging.info("Assigned permissions:")
                for perm in perm_objects:
                    logging.info(f"  - {perm.name}")

            return True

        except Exception as e:
            await session.rollback()
            logging.error(f"Error creating role: {e}")
            return False


def main():
    """Main function to run script."""
    parser = argparse.ArgumentParser(
        description="Create a role with optional permissions"
    )
    parser.add_argument("--name", help="Role name")
    parser.add_argument("--description", help="Role description")
    parser.add_argument(
        "--permissions", help="Comma-separated list of permission names"
    )
    parser.add_argument(
        "--no-input", action="store_true", help="Don't prompt for input"
    )
    parser.add_argument(
        "--list-permissions",
        action="store_true",
        help="List all available permissions and exit",
    )

    args = parser.parse_args()

    if args.list_permissions:
        asyncio.run(list_all_permissions())
        sys.exit(0)

    if args.no_input:
        if not args.name:
            logging.error("When using --no-input, you must provide --name")
            sys.exit(1)
        name = args.name
        description = args.description
    else:
        name = args.name or input("Role name: ")
        description = args.description
        if description is None:
            description = input("Role description (optional): ")
            if not description.strip():
                description = None

    if not name:
        logging.error("Role name is required.")
        sys.exit(1)

    permissions = None
    if args.permissions:
        permissions = [p.strip() for p in args.permissions.split(",") if p.strip()]
    elif not args.no_input:
        perm_input = input("Permissions (comma-separated, optional): ")
        if perm_input.strip():
            permissions = [p.strip() for p in perm_input.split(",") if p.strip()]

    success = asyncio.run(create_role(name, description, permissions))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
