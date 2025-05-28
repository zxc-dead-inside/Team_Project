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
    kafka_boostrap_servers: list[str] | str
    kafka_topic: str
    kafka_username: str
    kafka_password: str

    # Backoff
    retry_max_attempts: int = 10
    retry_base_delay: float = 0.1

    @field_validator("kafka_boostrap_servers", mode="before")
    def ensure_list(cls, v: str | list[str]) -> list[str]:
        """Parse string of Kafka Boostrap Server origins into list of URLs."""
        if isinstance(v, list):
            return v
        elif isinstance(v, str) and not v.startswith("["):
            # Return as strings to avoid validation issues
            return [url.strip() for url in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(
            "KAFKA_BOOSTRAP_SERVERS should be a comma-separated string of URLs"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()