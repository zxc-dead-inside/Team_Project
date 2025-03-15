"""Script to create a superuser account."""

import argparse
import asyncio
import getpass
import logging
import os
import sys
from typing import cast

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.core.logger import setup_logging
from src.db.database import Database
from src.db.models import Role, User
from src.db.models.audit_log import AuditLog


setup_logging()

settings = get_settings()
db_url: str = str(settings.database_url)

pwd_context: CryptContext = CryptContext(
    schemes=["argon2", "bcrypt"], deprecated="auto"
)


async def get_admin_role(session: AsyncSession) -> Role:
    """Get the admin role or create it if it doesn't exist."""
    result = await session.execute(select(Role).filter_by(name="admin"))
    role: Role | None = result.scalars().first()

    if not role:
        logging.info("Admin role not found, creating it...")
        role = Role(name="admin", description="Administrator with full access")
        session.add(role)
        await session.flush()
        logging.info("Admin role created")

    return cast(Role, role)


async def create_superuser(
    username: str, email: str, password: str, no_input: bool = False
) -> bool:
    """
    Create a superuser in the database.

    Args:
        username: Username for the superuser
        email: Email for the superuser
        password: Password for the superuser
        no_input: Whether to prompt for confirmation or not

    Returns:
        bool: True if superuser was created successfully, False otherwise
    """
    try:
        superuser_data = User(
            username=username,
            email=email,
            password=password,
        )
    except Exception as e:
        logging.error(f"Validation error: {e}")
        return False

    if not no_input:
        confirm: str = input(
            f"Create superuser '{superuser_data.username}' with email '{superuser_data.email}'? [y/N] "
        )
        if confirm.lower() not in ["y", "yes"]:
            logging.info("Superuser creation cancelled")
            return False

    db: Database = Database(db_url)

    async with db.session() as session:
        try:
            result = await session.execute(
                select(User).filter(
                    (User.username == superuser_data.username)
                    | (User.email == superuser_data.email)
                )
            )
            existing_user: User | None = result.scalars().first()

            if existing_user:
                if existing_user.username == superuser_data.username:
                    logging.error(
                        f"User with username '{superuser_data.username}' already exists."
                    )
                else:
                    logging.error(
                        f"User with email '{superuser_data.email}' already exists."
                    )
                return False

            admin_role: Role = await get_admin_role(session)

            hashed_password: str = pwd_context.hash(superuser_data.password)
            user: User = User(
                username=superuser_data.username,
                email=superuser_data.email,
                password=hashed_password,
                is_active=True,
                is_superuser=True,
            )

            user.roles = [admin_role]

            session.add(user)
            await session.flush()

            audit_log: AuditLog = AuditLog(
                action="create_superuser",
                resource_type="user",
                resource_id=user.id,
                details={
                    "username": user.username,
                    "email": user.email,
                    "created_by": "cli",
                },
            )
            session.add(audit_log)

            logging.info(f"Superuser '{superuser_data.username}' created successfully!")
            return True

        except Exception as e:
            await session.rollback()
            logging.error(f"Error creating superuser: {e}")
            return False


def main() -> None:
    """Main function to run script."""
    parser = argparse.ArgumentParser(description="Create a superuser")
    parser.add_argument("--username", help="Username for the superuser")
    parser.add_argument("--email", help="Email for the superuser")
    parser.add_argument("--password", help="Password for the superuser")
    parser.add_argument(
        "--no-input", action="store_true", help="Don't prompt for input or confirmation"
    )

    args: argparse.Namespace = parser.parse_args()

    # Default values for testing/development
    if args.no_input and not (args.username and args.email and args.password):
        logging.error(
            "When using --no-input, you must provide --username, --email, and --password"
        )
        sys.exit(1)

    username: str = args.username or input("Username: ")
    email: str = args.email or input("Email: ")
    password: str | None = args.password

    if not password:
        password = getpass.getpass("Password: ")
        password_confirm: str = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            logging.error("Passwords do not match")
            sys.exit(1)

    if not username or not email or not password:
        logging.error("Username, email, and password are required")
        sys.exit(1)

    success: bool = asyncio.run(
        create_superuser(username, email, password, args.no_input)
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
