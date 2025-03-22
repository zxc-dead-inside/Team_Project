"""
Script to set up the database and seed initial data if needed.
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import select, text
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
)


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.core.logger import setup_logging
from src.db.database import Database
from src.db.models import Permission, Role, User


setup_logging()
settings = get_settings()
db_url = str(settings.database_url)
scripts_dir = Path(__file__).parent


# Core roles that must exist
CORE_ROLES = {"admin", "anonymous", "user", "moderator", "subscriber"}

# Core permissions that must exist
CORE_PERMISSIONS = {
    "user_create",
    "user_read",
    "user_update",
    "user_delete",
    "role_create",
    "role_read",
    "role_update",
    "role_delete",
    "permission_read",
    "content_all",
    "content_recent",
    "view_public_content",
    "access_public_endpoints",
    "read_public_resources",
}


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_delay(60),
    retry=retry_if_exception_type(Exception),
    before_sleep=before_sleep_log(logging, logging.INFO),
)
async def check_database_connection():
    """Check if database is available, with exponential backoff."""
    db = Database(db_url)
    async with db.session() as session:
        await session.execute(text("SELECT 1"))
    return True


async def wait_for_database() -> bool:
    """Wait for database to be available with exponential backoff."""
    logging.info("Checking database connection...")

    try:
        await check_database_connection()
        logging.info("Database connection successful")
        return True
    except Exception as e:
        logging.error(f"Database not available after retrying: {e}")
        return False


async def check_superuser_exists() -> bool:
    """Check if at least one superuser exists."""
    db = Database(db_url)
    try:
        async with db.session() as session:
            result = await session.execute(
                select(User).filter(User.is_superuser == True)
            )
            return result.scalars().first() is not None
    except Exception as e:
        logging.error(f"Error checking for superuser: {e}")
        return False


async def check_roles_and_permissions() -> tuple[bool, set[str], set[str]]:
    """
    Check if all required roles and permissions exist.

    Returns:
        Tuple containing:
        - Boolean: True if all required roles and permissions exist
        - Set: Missing roles (empty if all exist)
        - Set: Missing permissions (empty if all exist)
    """
    db = Database(db_url)
    try:
        async with db.session() as session:
            # Check roles
            result = await session.execute(select(Role.name))
            existing_roles = {name for (name,) in result}
            missing_roles = CORE_ROLES - existing_roles

            # Check permissions
            result = await session.execute(select(Permission.name))
            existing_permissions = {name for (name,) in result}
            missing_permissions = CORE_PERMISSIONS - existing_permissions

            all_exist = len(missing_roles) == 0 and len(missing_permissions) == 0
            return all_exist, missing_roles, missing_permissions

    except Exception as e:
        logging.error(f"Error checking roles and permissions: {e}")
        return False, CORE_ROLES, CORE_PERMISSIONS


async def check_database_fully_initialized() -> bool:
    """Check if database is fully initialized with all required data."""
    # Check for superuser
    has_superuser = await check_superuser_exists()
    if not has_superuser:
        logging.info("No superuser found, database needs initialization")
        return False

    # Check for required roles and permissions
    all_exist, missing_roles, missing_permissions = await check_roles_and_permissions()
    if not all_exist:
        if missing_roles:
            logging.info(f"Missing required roles: {', '.join(missing_roles)}")
        if missing_permissions:
            logging.info(
                f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        return False

    return True


def run_script(script_name: str, *args) -> bool:
    """Run a script with arguments."""
    script_path = scripts_dir / script_name
    if not script_path.exists():
        logging.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    cmd.extend(args)

    logging.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logging.error(f"Script failed: {script_name}")
        logging.error(f"Error output: {result.stderr}")
        return False

    logging.info(f"Script completed successfully: {script_name}")
    return True


async def setup_database(skip_if_initialized: bool = True) -> None:
    """Set up database and seed initial data if needed."""
    logging.info("Starting database setup...")

    # First, check if database is available
    if not await wait_for_database():
        logging.error("Cannot continue without database connection")
        sys.exit(1)

    # Apply migrations - this is always safe to run
    logging.info("Applying database migrations...")
    if not run_script("apply_migrations.py"):
        logging.error("Failed to apply migrations")
        sys.exit(1)

    # Check if database is already initialized
    if skip_if_initialized:
        is_fully_initialized = await check_database_fully_initialized()
        if is_fully_initialized:
            logging.info("Database already fully initialized, skipping initialization")
            return
        else:
            logging.info("Database needs initialization or updates")

    # Seed permissions first
    logging.info("Seeding permissions...")
    if not run_script("seed_permissions.py"):
        logging.error("Failed to seed permissions")
        sys.exit(1)

    # Check if anonymous role exists, create if not
    _, missing_roles, _ = await check_roles_and_permissions()
    if "anonymous" in missing_roles:
        logging.info("Creating anonymous role...")
        if not run_script("create_anonymous_userrole.py"):
            logging.error("Failed to create anonymous role")
            sys.exit(1)
    else:
        logging.info("Anonymous role already exists")

    # Final verification
    is_fully_initialized = await check_database_fully_initialized()
    if is_fully_initialized:
        logging.info("Database setup completed successfully!")
    else:
        logging.error(
            "Database initialization incomplete - some components are missing"
        )
        _, missing_roles, missing_permissions = await check_roles_and_permissions()
        if missing_roles:
            logging.error(f"Missing roles: {', '.join(missing_roles)}")
        if missing_permissions:
            logging.error(f"Missing permissions: {', '.join(missing_permissions)}")
        if not await check_superuser_exists():
            logging.error("No superuser account found")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Set up database and seed initial data"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force initialization even if database appears to be initialized",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check database initialization status without modifying anything",
    )

    args = parser.parse_args()

    if args.check:
        asyncio.run(check_database_fully_initialized())
    else:
        asyncio.run(setup_database(skip_if_initialized=not args.force))
