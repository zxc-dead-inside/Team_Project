from functools import lru_cache
from typing import Optional
from pathlib import Path
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    db_user: str
    db_pass: str
    db_name: str
    db_host: str
    db_port: int
    database_url: Optional[str] = None

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str], info: ValidationInfo):
        if v:
            return v
        data = info.data
        return (
            f"postgresql+asyncpg://{data['db_user']}:"
            f"{data['db_pass']}@"
            f"{data['db_host']}:{data['db_port']}/"
            f"{data['db_name']}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
