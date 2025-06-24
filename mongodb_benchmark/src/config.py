from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class DataWeights(BaseSettings):
    """Веса длягеннерации данных"""
    users: float = 0.05
    movies: float = 0.15
    reviews: float = 0.25
    review_ratings: float = 0.3
    bookmarks: float = 0.1
    favorites: float = 0.05
    history: float = 0.1


class Operationeights(BaseSettings):
    """Веса для операций тестирования"""

    test_insert_review: float = 0.15
    test_get_reviews: float = 0.15
    test_add_rating: float = 0.15
    test_get_ratings_summary: float = 0.1
    test_add_bookmark: float = 0.1
    test_get_user_bookmarks: float = 0.1
    test_complex_query: float = 0.1
    test_top_movies_by_comments: float = 0.05
    test_top_helpful_reviews: float = 0.05
    test_top_users_by_comments: float = 0.05

class PostgresConfig(BaseSettings):
    """Конфигурация для postgres"""
    
    db_name: str = "movie_ugc"
    db_user: str = "postgres"
    password: str = "password"
    host: str = "localhost"
    port: int = 5432

class MongoConfig(BaseSettings):
    """онфигурация для Mongo"""

    db_name: str = "movie_ugc"
    db_username: str = "root"
    password: str = "password"
    host: str = "localhost"
    port: int = 27017
    authSource: str = "admin"


class Settings(BaseSettings):
    # Конфигурация PostgreSQL
    postgres_config: PostgresConfig = Field(default_factory=PostgresConfig)

    # Конфигурация MongoDB
    mongo_config: MongoConfig = Field(default_factory=MongoConfig)

    # Веса для генерации данных
    data_weights: DataWeights = Field(default_factory=DataWeights)

    # Веса для операций тестирования
    operation_weights: Operationeights = Field(default_factory=Operationeights)

    # Настройки для tqdm
    bar_forma: str = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]"
    colors: list = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        env_nested_delimiter = "__"
    )

settings = Settings()