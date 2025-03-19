"""
Script to initialize Alembic migrations structure.
"""

import subprocess
import sys
from pathlib import Path


def init_migrations() -> None:
    """Initialize Alembic migrations structure."""
    print("Initializing Alembic migrations structure...")

    # Get current directory
    current_dir = Path(__file__).parent.parent

    # Create migrations directory if it doesn't exist
    migrations_dir = current_dir / "migrations"
    if not migrations_dir.exists():
        migrations_dir.mkdir(exist_ok=True)
        print(f"Created migrations directory at {migrations_dir}")

    # Create alembic.ini if it doesn't exist
    alembic_ini = current_dir / "alembic.ini"
    if not alembic_ini.exists():
        # Run alembic init command
        result = subprocess.run(
            ["alembic", "init", "migrations"],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(current_dir),
        )

        if result.returncode != 0:
            print(f"Error initializing migrations: {result.stderr}")
            sys.exit(1)

        print(result.stdout)
        print("Migration structure initialized!")
    else:
        print(f"alembic.ini already exists at {alembic_ini}")

    print("Alembic structure initialized successfully!")


if __name__ == "__main__":
    init_migrations()
