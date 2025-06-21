"""
Seed script to create initial permissions for the application.
"""

import argparse
import asyncio
import json
import logging
import os
import sys

from sqlalchemy import select


# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.schemas.permissions import PermissionCreate
from src.core.config import get_settings
from src.core.logger import setup_logging
from src.db.database import Database
from src.db.models import Permission


setup_logging()

settings = get_settings()
db_url = str(settings.database_url)


# Default permissions that should be available in any installation
DEFAULT_PERMISSIONS = [
    {"name": "user_create", "description": "Create users"},
    {"name": "user_read", "description": "Read user details"},
    {"name": "user_update", "description": "Update users"},
    {"name": "user_delete", "description": "Delete users"},
    {"name": "role_create", "description": "Create roles"},
    {"name": "role_read", "description": "Read roles"},
    {"name": "role_update", "description": "Update roles"},
    {"name": "role_delete", "description": "Delete roles"},
    {"name": "permission_read", "description": "Read permissions"},
    {"name": "content_all", "description": "Access all content"},
    {"name": "content_recent", "description": "Access recent content"},
    {"name": "settings_read", "description": "Read system settings"},
    {"name": "settings_update", "description": "Update system settings"},
    {"name": "superuser_manage", "description": "Manage superuser privileges"},
    {"name": "audit_log_read", "description": "Read audit logs"},
    # Anonymous user permissions
    {"name": "view_public_content",
     "description": "Permission to view public content"},
    {"name": "access_public_endpoints",
     "description": "Permission to access public endpoints"},
    {"name": "read_public_resources",
     "description": "Permission to read public resources"},
]


async def list_permissions() -> None:
    """List all permissions in the database."""
    db = Database(db_url)

    async with db.session() as session:
        result = await session.execute(select(Permission).order_by(Permission.name))
        permissions = result.scalars().all()

        if not permissions:
            logging.info("No permissions found in the database.")
            return

        logging.info("\nExisting permissions:")
        logging.info("-" * 80)
        logging.info(f"{'NAME':<30} {'DESCRIPTION':<50}")
        logging.info("-" * 80)

        for permission in permissions:
            description = permission.description or ""
            logging.info(f"{permission.name:<30} {description:<50}")


async def create_permission(name: str, description: str | None = None) -> bool:
    """
    Create a single permission.

    Args:
        name: Permission name
        description: Permission description

    Returns:
        bool: Success status
    """
    try:
        validated_data = PermissionCreate(name=name, description=description)
    except Exception as e:
        logging.error(f"Validation error for permission '{name}': {e}")
        return False

    db = Database(db_url)

    async with db.session() as session:
        try:
            result = await session.execute(
                select(Permission).filter(Permission.name == validated_data.name)
            )
            existing_permission = result.scalars().first()

            if existing_permission:
                logging.info(
                    f"Permission '{validated_data.name}' already exists. Skipping."
                )
                return True

            permission = Permission(
                name=validated_data.name,
                description=validated_data.description,
            )

            session.add(permission)
            await session.commit()

            logging.info(f"Permission '{validated_data.name}' created successfully.")
            return True

        except Exception as e:
            await session.rollback()
            logging.error(f"Error creating permission '{validated_data.name}': {e}")
            return False


async def seed_default_permissions(dry_run: bool = False) -> dict[str, int]:
    """
    Seed default permissions.

    Args:
        dry_run: If True, just print what would be done without making changes

    Returns:
        Dict with counts of successful and failed operations
    """
    results = {"created": 0, "failed": 0, "skipped": 0, "existing": 0}

    if dry_run:
        logging.info("DRY RUN: The following permissions would be created:")
        for perm_data in DEFAULT_PERMISSIONS:
            logging.info(f"  - {perm_data['name']}: {perm_data['description']}")
        return results

    db = Database(db_url)
    existing_permissions: set[str] = set()

    async with db.session() as session:
        result = await session.execute(select(Permission.name))
        existing_permissions = {name for (name,) in result}

    for perm_data in DEFAULT_PERMISSIONS:
        if perm_data["name"] in existing_permissions:
            logging.info(f"Permission '{perm_data['name']}' already exists. Skipping.")
            results["existing"] += 1
            continue

        success = await create_permission(
            name=perm_data["name"], description=perm_data["description"]
        )

        if success:
            results["created"] += 1
        else:
            results["failed"] += 1

    return results


async def seed_permissions_from_file(
    file_path: str, dry_run: bool = False
) -> dict[str, int]:
    """
    Seed permissions from a JSON or CSV file.

    Args:
        file_path: Path to permissions file
        dry_run: If True, just print what would be done without making changes

    Returns:
        Dict with counts of successful and failed operations
    """
    import csv

    results = {"created": 0, "failed": 0, "skipped": 0, "existing": 0}
    permissions_data = []

    try:
        if file_path.endswith(".json"):
            with open(file_path) as f:
                permissions_data = json.load(f)

            if not isinstance(permissions_data, list):
                logging.error("JSON file must contain a list of permission objects")
                return results

        elif file_path.endswith(".csv"):
            with open(file_path) as f:
                reader = csv.DictReader(f)
                permissions_data = list(reader)

            if not permissions_data or "name" not in permissions_data[0]:
                logging.error("CSV file must have a 'name' column")
                return results
        else:
            logging.error("Unsupported file format. Please use .json or .csv")
            return results

        if dry_run:
            logging.info(
                f"DRY RUN: The following permissions would be created from {file_path}:"
            )
            for perm_data in permissions_data:
                if "name" in perm_data:
                    desc = perm_data.get("description", "")
                    logging.info(f"  - {perm_data['name']}: {desc}")
            return results

        db = Database(db_url)
        existing_permissions: set[str] = set()

        async with db.session() as session:
            result = await session.execute(select(Permission.name))
            existing_permissions = {name for (name,) in result}

        for perm_data in permissions_data:
            if "name" not in perm_data:
                logging.error(
                    f"Invalid permission data: {perm_data} - missing 'name' field"
                )
                results["failed"] += 1
                continue

            if perm_data["name"] in existing_permissions:
                logging.info(
                    f"Permission '{perm_data['name']}' already exists. Skipping."
                )
                results["existing"] += 1
                continue

            success = await create_permission(
                name=perm_data["name"], description=perm_data.get("description")
            )

            if success:
                results["created"] += 1
            else:
                results["failed"] += 1

    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")

    return results


async def main(args):
    """Main function to run script."""
    if args.list:
        await list_permissions()
        return

    logging.info("Starting permission seeding process...")

    if args.file:
        logging.info(f"Seeding permissions from file: {args.file}")
        results = await seed_permissions_from_file(args.file, args.dry_run)
    else:
        logging.info("Seeding default permissions...")
        results = await seed_default_permissions(args.dry_run)

    if args.dry_run:
        logging.info("DRY RUN: No changes were made to the database.")
    else:
        logging.info(
            f"Permissions seeded: {results['created']} created, "
            f"{results['existing']} already existed, {results['failed']} failed"
        )

    if args.list_after and not args.dry_run:
        logging.info("\nListing all permissions after seeding:")
        await list_permissions()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed permissions for the application")
    parser.add_argument(
        "--file", help="JSON or CSV file containing permissions to seed"
    )
    parser.add_argument(
        "--list", action="store_true", help="List existing permissions and exit"
    )
    parser.add_argument(
        "--list-after", action="store_true", help="List permissions after seeding"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't make any changes, just print what would be done",
    )

    parsed_args = parser.parse_args()
    asyncio.run(main(parsed_args))
