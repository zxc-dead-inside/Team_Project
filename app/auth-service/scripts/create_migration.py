"""
Script to create an Alembic migration.
"""

import subprocess
import sys
from pathlib import Path


def create_migration(message: str = "Initial migration") -> None:
    """
    Create a new Alembic migration.

    Args:
        message: Migration message
    """
    print(f"Creating migration: {message}")

    # Create migrations directory if it doesn't exist
    migrations_dir = Path("migrations")
    versions_dir = migrations_dir / "versions"

    if not migrations_dir.exists():
        print("Creating migrations directory")
        migrations_dir.mkdir(exist_ok=True)

    if not versions_dir.exists():
        print("Creating versions directory")
        versions_dir.mkdir(exist_ok=True)

    # Run Alembic command
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", message],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error creating migration: {result.stderr}")
        sys.exit(1)

    print(result.stdout)
    print("Migration created successfully!")


if __name__ == "__main__":
    # Get message from command line arguments
    message = "Initial migration"
    if len(sys.argv) > 1:
        message = sys.argv[1]

    create_migration(message)
