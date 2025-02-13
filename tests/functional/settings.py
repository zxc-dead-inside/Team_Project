from pydantic import Field
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    # Elasticsearch settings
    es_host: str = Field(
        default="elasticsearch", json_schema_extra={"env": "elasticsearch_host"}
    )
    es_port: int = Field(default=9200, json_schema_extra={"env": "elasticsearch_port"})

    movie_index: str = Field(default="movies")
    genre_index: str = Field(default="genres")

    person_index: str = Field(default="persons")
    person_endpoint: str = Field(default="/api/v1/persons/")

    # Redis settings
    redis_host: str = Field(
        default="theatre-redis", json_schema_extra={"env": "redis_host"}
    )
    redis_port: int = Field(default=6379, json_schema_extra={"env": "redis_port"})

    # FastAPI service settings
    api_host: str = Field(default="fastapi")
    api_port: int = Field(default=9000)

    @property
    def es_url(self) -> str:
        return f"http://{self.es_host}:{self.es_port}"

    @property
    def service_url(self) -> str:
        return f"{self.api_host}:{self.api_port}"


test_settings = TestSettings()
