"""Configuration settings for the application."""

from functools import lru_cache

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    project_name: str = "Auth Service"
    api_v1_prefix: str = "/api/v1"
    environment: str = Field(default="development")
    log_level: str = "INFO"

    # Authentication
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    email_token_ttl_seconds: int = 600  # 10 minutes
    secrets_path: str = 'secrets'
    private_key: str | None = None
    public_key: str | None = None

    @field_validator("private_key", mode="before")
    def assemble_private_key(cls, v: str | None, values) -> str:
        """Assemble private_key from folder"""
        if v:
            return v
        try:
            return open(
                values.data.get("secrets_path") + "/private_key.pem",
                'rb'
                ).read()
        except Exception:
            raise ValueError("SECRETS_PATH should contains private_key.pem")

    @field_validator("public_key", mode="before")
    def assemble_public_key(cls, v: str | None, values) -> str:
        """Assemble public_key.pem exists from folder"""
        if v:
            return v
        try:
            return open(
                values.data.get("secrets_path") + "/public_key.pem",
                'rb'
                ).read()
        except Exception:
            raise ValueError("SECRETS_PATH should contains public_key.pem")

    # PostgreSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "db"
    postgres_port: str = "5432"
    database_url: PostgresDsn | None = None

    # Redis
    cache_ttl: int = 3600

    @field_validator("database_url", mode="before")
    def assemble_db_url(cls, v: str | None, values) -> str:
        """Assemble database URL if not provided."""
        if v:
            return v

        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.data.get("postgres_user"),
            password=values.data.get("postgres_password"),
            host=values.data.get("postgres_host"),
            port=int(values.data.get("postgres_port")),
            path=f"{values.data.get('postgres_db') or ''}",
        )

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_url: RedisDsn | None = None

    @field_validator("redis_url", mode="before")
    def assemble_redis_url(cls, v: str | None, values) -> str:
        """Assemble Redis URL if not provided."""
        if v:
            return v

        password_part = ""
        if values.data.get("redis_password"):
            password_part = f":{values.data.get('redis_password')}@"

        return f"redis://{password_part}{values.data.get('redis_host')}:{values.data.get('redis_port')}/0"

    # CORS
    cors_origins: list[AnyHttpUrl] | list[str] = []

    @field_validator("cors_origins", mode="before")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse string CORS origins into list of URLs."""
        if isinstance(v, str) and not v.startswith("["):
            # Return as strings to avoid validation issues
            origins = [url.strip() for url in v.split(",")]
            # Ensure each URL has a scheme
            for i, origin in enumerate(origins):
                if not origin.startswith(("http://", "https://")):
                    origins[i] = f"http://{origin}"
            return origins
        elif isinstance(v, list):
            return v
        raise ValueError("CORS_ORIGINS should be a comma-separated string of URLs")

    # Public paths
    public_paths: str | list[str] = []
    private_path_prefixes: str | list[str] | None = []

    @field_validator("public_paths", mode="before")
    def assemble_public_paths(cls, v: str | list[str]) -> list[str]:
        try:
            """Parse string PUBLIC_PATHS origins into list of PUBLIC_PATHs."""
            if isinstance(v, str) and not v.startswith("["):
                # Return as strings to avoid validation issues
                return [url.strip() for url in v.split(",")]
            elif isinstance(v, list):
                return v
            raise ValueError("PUBLIC_PATHS should be a comma-separated string of PATHs")
        except Exception:
            exit(1)
    
    @field_validator("private_path_prefixes", mode="before")
    def assemble_private_path_prefixes(
        cls, v: str | list[str]) -> list[str] | None:
        """Parse string PRIVATE_PATHS_PREFIX origins into list of PATHs."""
        if not v: return None
        if isinstance(v, str) and not v.startswith("["):
            # Return as strings to avoid validation issues
            return [url.strip() for url in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError("PUBLIC_PATHS should be a comma-separated string of PRIVATE_PATH_PREFIXES")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()