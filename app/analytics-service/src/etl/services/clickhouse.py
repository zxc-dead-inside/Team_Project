import logging
from datetime import datetime
from typing import Any

from clickhouse_driver import Client
from src.core.logger import setup_logging


setup_logging()


class ClickHouseClient:
    """Client for interacting with ClickHouse database."""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        """Initialize ClickHouse client.

        Args:
            host: ClickHouse server hostname
            port: ClickHouse server port
            user: Username for authentication
            password: Password for authentication
            database: Database name
        """
        self.client = Client(
            host=host, port=port, user=user, password=password, database=database
        )
        self.database = database
        logging.info(f"Initialized ClickHouse client for {database} database")

    def healthcheck(self) -> dict[str, Any]:
        """Check if ClickHouse is available.

        Returns:
            Dict with status and details
        """
        try:
            result = self.client.execute("SELECT 1")
            if result and result[0][0] == 1:
                return {"status": True, "detail": ""}
            return {"status": False, "detail": "Unexpected response from ClickHouse"}
        except Exception as e:
            return {"status": False, "detail": str(e)}

    def create_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        # Create user_actions table
        self.client.execute("""
            CREATE TABLE IF NOT EXISTS user_actions (
                user_id String,
                movie_id String,
                action_type Enum(
                    'view_start' = 1,
                    'view_end' = 2,
                    'pause' = 3,
                    'seek' = 4,
                    'rating' = 5,
                    'favorite' = 6
                ),
                timestamp DateTime64(3),
                duration_seconds Nullable(Float64),
                current_time Nullable(Float64),
                percent_watched Nullable(Float64),
                device_type Nullable(String)
            )
            ENGINE = MergeTree()
            PARTITION BY toYYYYMM(timestamp)
            ORDER BY (user_id, movie_id, timestamp)
        """)

        logging.info("Created necessary ClickHouse tables")

    def insert_user_actions(self, actions: list[dict[str, Any]]) -> int:
        """Insert user actions into ClickHouse.

        Args:
            actions: List of user action dictionaries

        Returns:
            Number of inserted rows
        """
        if not actions:
            return 0

        # Transform data for insertion
        rows = []
        for action in actions:
            metadata = action.get("metadata", {})
            timestamp_ms = action["timestamp"]
            if isinstance(timestamp_ms, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
            else:
                timestamp = timestamp_ms

            row = (
                action["user_id"],
                action["movie_id"],
                action["action_type"],
                timestamp,
                metadata.get("duration_seconds"),
                metadata.get("current_time"),
                metadata.get("percent_watched"),
                metadata.get("device_type"),
            )
            rows.append(row)

        # Insert data
        self.client.execute(
            """
            INSERT INTO user_actions (
                user_id, movie_id, action_type, timestamp,
                duration_seconds, current_time, percent_watched, device_type
            ) VALUES
            """,
            rows,
        )

        logging.info(f"Inserted {len(rows)} user actions into ClickHouse")
        return len(rows)
