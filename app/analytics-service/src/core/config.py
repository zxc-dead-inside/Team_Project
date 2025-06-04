"""Configuration settings for the application."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    project_name: str = "Analytics Service"
    environment: str = Field(default="development")
    log_level: str = "INFO"

    # Kafka connection settings
    kafka_bootstrap_servers: list[str] | str
    kafka_topic: str
    kafka_username: str = ""
    kafka_password: str = ""
    kafka_group_id: str = "analytics-etl-group"

    # ClickHouse connection settings
    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 9000
    clickhouse_user: str = "default"
    clickhouse_password: str = "password"
    clickhouse_database: str = "analytics"

    # ETL settings
    etl_batch_size: int = 100
    etl_batch_timeout: float = 5.0

    # Backoff
    retry_max_attempts: int = 10
    retry_base_delay: float = 0.1

    @field_validator("kafka_bootstrap_servers", mode="before")
    def ensure_list(cls, v: str | list[str]) -> list[str]:
        """Parse string of Kafka Boostrap Server origins into list of URLs."""

        if isinstance(v, list):
            return v
        elif isinstance(v, str) and not v.startswith("["):
            return [url.strip() for url in v.split(",")]
        raise ValueError(
            "KAFKA_BOOTSTRAP_SERVERS should be a comma-separated string of URLs"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()