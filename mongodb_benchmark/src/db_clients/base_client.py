import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from faker import Faker
from pydantic import BaseModel, Field

from config import settings


class PerformanceResult(BaseModel):
    operation: str
    execution_time_ms: float
    records_processed: int
    timestamp: datetime = Field(default_factory=datetime.now)


class DBClient(ABC):
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.fake = Faker()
        self.fake.seed_instance(42)
        self.data_generated = False
        self.user_ids: list[int] = []
        self.movie_ids: list[int] = []
        self.review_ids: list[int] = []

    @abstractmethod
    def connect(self):
        """Подключение к БД."""
        pass

    @abstractmethod
    def disconnect(self):
        """Отключение от БД."""
        pass

    @abstractmethod
    def initialize_schema(self):
        """Инициализация схемы."""
        pass

    @abstractmethod
    def generate_test_data(self, total_records: int):
        """Генерация тестовых данных."""
        pass

    @abstractmethod
    def load_ids_cache(self):
        """Загрузка ID в кеш для использования в тестах"""
        pass

    @abstractmethod
    def cleanup(self):
        """Полная очистка всех данных в базе"""
        pass

    @abstractmethod
    def test_insert_review(self) -> int:
        """Добавление ревью."""
        pass

    @abstractmethod
    def test_get_reviews(self) -> int:
        """Получение ревью."""
        pass

    @abstractmethod
    def test_add_rating(self) -> int:
        """Добавление рейтинга ревью."""
        pass

    @abstractmethod
    def test_get_ratings_summary(self) -> int:
        """"""
        pass

    @abstractmethod
    def test_add_bookmark(self) -> int:
        """Добавление закладки."""
        pass

    @abstractmethod
    def test_get_user_bookmarks(self) -> int:
        """Получение закладок."""
        pass

    @abstractmethod
    def test_complex_query(self) -> int:
        """Сложный аналитический запрос"""
        pass

    @abstractmethod
    def test_top_movies_by_comments(self) -> int:
        """Топ-10 фильмов с наибольшим количеством комментариев"""
        pass

    @abstractmethod
    def test_top_helpful_reviews(self) -> int:
        """Топ-5 самых полезных комментариев к фильму (лайки > дизлайки)"""
        pass

    @abstractmethod
    def test_top_users_by_comments(self) -> int:
        """Топ-10 пользователей с наибольшим количеством оставленных комментариев"""
        pass

    def _calculate_record_counts(self, total_records: int) -> Dict[str, int]:
        """Рассчитывает количество записей для каждой сущности на основе весов"""
        data_weights = settings.data_weights.model_dump()
        return {
            entity: int(total_records * weight)
            for entity, weight in data_weights.items()
        }

    def _generate_uuid(self) -> str:
        """Генерирует UUID в формате, подходящем для конкретной СУБД"""
        return str(uuid.uuid4())
