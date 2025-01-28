from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQL_HOST: str
    SQL_PORT: int

    # Elasticsearch settings
    ELASTICSEARCH_HOST: str = "elasticsearch"
    ELASTICSEARCH_PORT: int = 9200

    # ETL settings
    BATCH_SIZE: int = 100
    STATE_FILE_PATH: Path = Path("state/etl_state.json")

    SLEEP_TIME: int = 60

    @property
    def postgres_dsn(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.SQL_HOST}:{self.SQL_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
