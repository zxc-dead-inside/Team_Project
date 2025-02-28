"""
Script to apply Alembic migrations.
"""

import os
import subprocess
import sys
from pathlib import Path


def find_alembic_ini():
    current_dir = Path(__file__).parent

    # Try several possible locations
    possible_paths = [
        current_dir.parent / "alembic.ini",  # Project root
        current_dir.parent.parent / "alembic.ini",  # One level up
        current_dir / "alembic.ini",  # Same directory
        current_dir.parent / "core" / "alembic.ini",  # In core directory
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # If not found in common locations, search upward
    search_dir = current_dir
    for _ in range(5):  # Limit search depth to 5 levels up
        search_dir = search_dir.parent
        potential_path = search_dir / "alembic.ini"
        if potential_path.exists():
            return potential_path

    return None


def apply_migrations() -> None:
    """Apply Alembic migrations to the database."""
    print("Applying migrations...")

    # Find alembic.ini
    alembic_ini_path = find_alembic_ini()

    if not alembic_ini_path:
        print("Error: Could not find alembic.ini.")
        print("Current directory:", os.getcwd())
        print("Script location:", Path(__file__).absolute())
        sys.exit(1)

    print(f"Found alembic.ini at: {alembic_ini_path}")

    # Run Alembic command with explicit config path
    result = subprocess.run(
        ["alembic", "-c", str(alembic_ini_path), "upgrade", "head"],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error applying migrations: {result.stderr}")
        sys.exit(1)

    print(result.stdout)
    print("Migrations applied successfully!")


if __name__ == "__main__":
    # Make sure we can find the modules
    sys.path.insert(0, str(Path(__file__).parent.parent))

    apply_migrations()
