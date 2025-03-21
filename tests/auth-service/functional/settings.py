from string import Template
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


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
    redis_url: str | None = None


    # FastAPI service settings
    auth_host: str = Field(default="auth-service")
    auth_port: int = Field(default=8100)

    @property
    def service_url(self) -> str:
        return f"{self.auth_host}:{self.auth_port}"


test_settings = TestSettings()
