"""Script to create a superuser account."""

import argparse
import asyncio
import getpass
import logging
import os
import sys

from passlib.context import CryptContext
from sqlalchemy import select


# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.core.logger import setup_logging
from src.db.database import Database
from src.db.models import Role, User
from src.db.models.audit_log import AuditLog


setup_logging()

settings = get_settings()
db_url = str(settings.database_url)

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


async def get_admin_role(session):
    """Get the admin role or create it if it doesn't exist."""
    result = await session.execute(select(Role).filter_by(name="admin"))
    role = result.scalars().first()

    if not role:
        logging.info("Admin role not found, creating it...")
        role = Role(name="admin", description="Administrator with full access")
        session.add(role)
        await session.flush()
        logging.info("Admin role created")

    return role


async def create_superuser(username, email, password, no_input=False) -> None:
    """
    Create a superuser in the database.

    Args:
        username: Username for the superuser
        email: Email for the superuser
        password: Password for the superuser
        no_input: Whether to prompt for confirmation or not
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
        confirm = input(
            f"Create superuser '{superuser_data.username}' with email '{superuser_data.email}'? [y/N] "
        )
        if confirm.lower() not in ["y", "yes"]:
            logging.info("Superuser creation cancelled")
            return False

    db = Database(db_url)

    async with db.session() as session:
        try:
            result = await session.execute(
                select(User).filter(
                    (User.username == superuser_data.username)
                    | (User.email == superuser_data.email)
                )
            )
            existing_user = result.scalars().first()

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

            admin_role = await get_admin_role(session)

            hashed_password = pwd_context.hash(superuser_data.password)
            user = User(
                username=superuser_data.username,
                email=superuser_data.email,
                password=hashed_password,
                is_active=True,
                is_superuser=True,
            )

            user.roles = [admin_role]

            session.add(user)
            await session.flush()

            audit_log = AuditLog(
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


def main():
    """Main function to run script."""
    parser = argparse.ArgumentParser(description="Create a superuser")
    parser.add_argument("--username", help="Username for the superuser")
    parser.add_argument("--email", help="Email for the superuser")
    parser.add_argument("--password", help="Password for the superuser")
    parser.add_argument(
        "--no-input", action="store_true", help="Don't prompt for input or confirmation"
    )

    args = parser.parse_args()

    # Default values for testing/development
    if args.no_input and not (args.username and args.email and args.password):
        logging.error(
            "When using --no-input, you must provide --username, --email, and --password"
        )
        sys.exit(1)

    username = args.username or input("Username: ")
    email = args.email or input("Email: ")
    password = args.password

    if not password:
        password = getpass.getpass("Password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            logging.error("Passwords do not match")
            sys.exit(1)

    if not username or not email or not password:
        logging.error("Username, email, and password are required")
        sys.exit(1)

    success = asyncio.run(create_superuser(username, email, password, args.no_input))

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
