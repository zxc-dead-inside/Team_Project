"""
Script to initialize Alembic migrations structure.
"""

import subprocess
import sys
from pathlib import Path


# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


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

    # Update env.py to include models
    env_py = migrations_dir / "env.py"
    if env_py.exists():
        update_env_py(env_py)

    print("Alembic structure initialized successfully!")


def update_env_py(env_py_path: Path) -> None:
    """Update env.py to include our models."""
    with open(env_py_path, "r") as f:
        content = f.read()

    # Check if our imports are already in there
    if "from src.db.database import Base" not in content:
        # Add imports
        import_section = """
        # Import the models so that Base has them
        from src.db.database import Base
        from src.db.models import *
        from src.core.config import settings

        # Set the database URL in the alembic config
        config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        """
        # Find the target_metadata line
        target_line = "target_metadata = None"
        new_content = content.replace(
            target_line, f"{import_section}\ntarget_metadata = Base.metadata"
        )

        # Write updated content
        with open(env_py_path, "w") as f:
            f.write(new_content)

        print("Updated env.py with model imports")


if __name__ == "__main__":
    init_migrations()
