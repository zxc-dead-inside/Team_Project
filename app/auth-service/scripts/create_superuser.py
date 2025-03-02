"""
Script to create a superuser from the command line.
"""

import argparse
import asyncio
import getpass
import os
import sys

from passlib.context import CryptContext
from sqlalchemy import select


# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.db.database import Database
from src.db.models import Role, User


settings = get_settings()
db_url = str(settings.database_url)


# Set up password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_admin_role(session):
    """Get the admin role or create it if it doesn't exist."""
    result = await session.execute(select(Role).filter_by(name="admin"))
    role = result.scalars().first()

    if not role:
        role = Role(name="admin", description="Administrator with full access")
        session.add(role)
        await session.flush()

    return role


async def create_superuser(username, email, password) -> None:
    """
    Create a superuser in the database.

    Args:
        username: Username for the superuser
        email: Email for the superuser
        password: Password for the superuser
    """
    print(f"Creating superuser: {username} ({email})")
    db = Database(db_url)

    async with db.session() as session:
        try:
            # Check if user already exists
            result = await session.execute(
                select(User).filter((User.username == username) | (User.email == email))
            )
            existing_user = result.scalars().first()

            if existing_user:
                print(
                    f"User with username '{username}' or email '{email}' already exists."
                )
                return

            # Get admin role
            admin_role = await get_admin_role(session)

            # Create user
            hashed_password = pwd_context.hash(password)
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,
            )

            # Add admin role to user
            user.roles.append(admin_role)

            session.add(user)

            print(f"Superuser '{username}' created successfully!")

        except Exception as e:
            print(f"Error creating superuser: {e}")
            raise


def main():
    """Main function to run script."""
    parser = argparse.ArgumentParser(description="Create a superuser")
    parser.add_argument("--username", help="Username for the superuser")
    parser.add_argument("--email", help="Email for the superuser")
    parser.add_argument("--password", help="Password for the superuser")

    args = parser.parse_args()

    # Prompt for missing arguments
    username = args.username or input("Username: ")
    email = args.email or input("Email: ")
    password = args.password or getpass.getpass("Password: ")

    if not username or not email or not password:
        print("Username, email, and password are required.")
        sys.exit(1)

    asyncio.run(create_superuser(username, email, password))


if __name__ == "__main__":
    main()
