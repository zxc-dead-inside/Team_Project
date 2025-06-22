from datetime import timedelta

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "Movies API"
    api_v1_str: str = "/api/v1"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000"
    ]

    # Elasticsearch
    elasticsearch_host: str = (
        "elasticsearch"
    )
    elasticsearch_port: int = 9200
    elasticsearch_username: str = ""
    elasticsearch_password: str = ""

    #Redis
    redis_host: str
    redis_port: int
    redis_cache_db: int

    @computed_field
    def redis_url(self) -> str:
        """Build Redis URL from components."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_cache_db}"

    # Movie index
    movie_index: str = "movies"
    genre_index: str = "genres"
    person_index: str = "persons"

    default_ttl: timedelta = timedelta(minutes=15)

    # Auth service settings
    auth_service_url: str = "http://auth_service_api:8100"
    auth_service_timeout: int = 3  # seconds
    emergency_mode: bool = False  # Set to True to bypass auth service for all requests

    # Token settings
    token_blacklist_ttl: int = 86400
    
    class Config:
        env_file = ".env"


settings = Settings() # type: ignore
