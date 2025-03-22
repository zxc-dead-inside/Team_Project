from pydantic import Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):

    # PostgreSQL settings
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "db"
    postgres_port: str = "5432"
    database_url: str | None = None
    
    # Redis settings
    redis_host: str = Field(
        default="auth-redis", json_schema_extra={"env": "redis_host"}
    )
    redis_port: int = Field(default=6379, json_schema_extra={"env": "redis_port"})
    redis_password: str | None = Field(default="redis", json_schema_extra={"env": "redis_password"})
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


    # FastAPI service settings
    auth_host: str = Field(default="auth-service")
    auth_port: int = Field(default=8100)

    @property
    def service_url(self) -> str:
        return f"{self.auth_host}:{self.auth_port}"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # case_sensitive=True,
    )


test_settings = TestSettings()
