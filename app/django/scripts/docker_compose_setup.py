"""Script to wait for database and apply migrations."""

import logging
import os
import subprocess
import sys

import psycopg
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("docker_compose_setup")


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(60),
    retry=retry_if_exception_type(psycopg.OperationalError),
)
def check_database_connection():
    """Check if database is available, with exponential backoff."""
    logger.info("Attempting database connection...")
    connection = psycopg.connect(
        dbname=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        host=os.environ.get("SQL_HOST"),
        port=os.environ.get("SQL_PORT"),
    )
    connection.close()
    logger.info("Database connection successful!")
    return True


def run_migrations():
    """Run Django migrations."""
    logger.info("Running database migrations...")
    try:
        subprocess.run(["python", "manage.py", "migrate"], check=True)
        logger.info("Migrations completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error applying migrations: {e}")
        sys.exit(1)


def run_collectstatic():
    """Collect static files."""
    logger.info("Collecting static files...")
    try:
        subprocess.run(
            ["python", "manage.py", "collectstatic", "--noinput"], check=True
        )
        logger.info("Static files collected successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error collecting static files: {e}")
        # Not exiting here as this is less critical than migrations


def main():
    """Main function to coordinate database setup."""
    logger.info("Starting database setup...")

    try:
        # Wait for database to be available
        check_database_connection()

        # Run migrations
        run_migrations()

        # Collect static files
        run_collectstatic()

        logger.info("Database setup completed successfully")
    except Exception as e:
        logger.error(f"Error during database setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
