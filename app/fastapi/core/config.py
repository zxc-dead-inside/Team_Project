from datetime import timedelta
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
        "elasticsearch"  # if in development then "host.docker.internal"
    )
    elasticsearch_port: int = 9200
    elasticsearch_username: str = ""
    elasticsearch_password: str = ""

    #Redis
    redis_host: str
    redis_port: int
    redis_cache_db: int

    # Movie index
    movie_index: str = "movies"
    genre_index: str = "genres"
    person_index: str = "persons"

    default_ttl: timedelta = timedelta(minutes=15)

    class Config:
        env_file = ".env"


settings = Settings()
