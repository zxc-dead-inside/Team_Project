from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Movies API"
    API_V1_STR: str = "/api/v1"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000"
    ]

    # Elasticsearch
    ELASTICSEARCH_HOST: str = (
        "elasticsearch"  # if in development then "host.docker.internal"
    )
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USERNAME: str = ""
    ELASTICSEARCH_PASSWORD: str = ""

    # Movie index
    MOVIE_INDEX: str = "movies"
    GENRE_INDEX: str = "genres"

    class Config:
        env_file = ".env"


settings = Settings()
