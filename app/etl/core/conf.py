from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    elasticsearch_index: str = "movies"
    elasticsearch_port: int = 9200
    elasticsearch_host: str = "elasticsearch"
    sql_port: int = 5432
    sql_host: str = "theatre-db"
    postgres_db: str = "theatre"
    postgres_password: str = "secret"
    postgres_user: str = "postgres"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"



config = AppConfig()