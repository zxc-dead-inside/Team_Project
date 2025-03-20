from string import Template
from pydantic import Field, PostgresDsn, field_validator, RedisDsn
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    # Redis
    redis_host: str = "redis"
    redis_port: int = 6380
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


    # PostgreSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "db"
    postgres_port: str = "5433"
    database_url: PostgresDsn | None = None

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

    # Auth-api service settings
    api_host: str = Field(default="test-api")
    api_port: int = Field(default=9000)

    # Seraching film settings
    film_count: int = 50
    film_not_found_len: int  = 1
    film_search_endpoint: Template = Template(
        '/api/v1/films/search?query=${search}&page_number=1&page_size=50')
    

    # Seraching person settings
    person_count: int = 50
    person_not_found_len: int  = 1
    person_search_endpoint: Template = Template(
        '/api/v1/persons/search?query=${search}&page_number=1&page_size=50')

    @property
    def es_url(self) -> str:
        return f"http://{self.es_host}:{self.es_port}"

    @property
    def service_url(self) -> str:
        return f"{self.api_host}:{self.api_port}"


test_settings = TestSettings()
