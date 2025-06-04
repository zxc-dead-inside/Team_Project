"""
Модели данных для исследования производительности БД
Используется Pydantic V2 для валидации данных
"""

from datetime import date, datetime
from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PositiveInt


class Genre(str, Enum):
    """Жанры фильмов"""

    ACTION = "action"
    COMEDY = "comedy"
    DRAMA = "drama"
    HORROR = "horror"
    ROMANCE = "romance"
    THRILLER = "thriller"
    DOCUMENTARY = "documentary"
    ANIMATION = "animation"
    FANTASY = "fantasy"
    SCIENCE_FICTION = "science_fiction"


class Country(str, Enum):
    """Страны"""

    RU = "RU"
    US = "US"
    UK = "UK"
    DE = "DE"
    FR = "FR"
    IT = "IT"
    ES = "ES"
    JP = "JP"
    KR = "KR"
    CN = "CN"


class User(BaseModel):
    """Модель пользователя"""

    user_id: UUID = Field(default_factory=uuid4, description="Уникальный UUID пользователя")
    email: EmailStr = Field(description="Email пользователя")
    username: Annotated[
        str, Field(min_length=3, max_length=50, description="Имя пользователя")
    ]
    first_name: Annotated[str, Field(max_length=100, description="Имя")]
    last_name: Annotated[str, Field(max_length=100, description="Фамилия")]
    country: Country = Field(description="Страна")
    birth_date: date = Field(description="Дата рождения")
    registration_date: datetime = Field(description="Дата регистрации")
    is_premium: bool = Field(default=False, description="Премиум подписка")

    @property
    def age(self) -> int:
        """Вычисляет возраст пользователя"""
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )


class Movie(BaseModel):
    """Модель фильма"""

    model_config = ConfigDict(str_strip_whitespace=True)

    movie_id: PositiveInt = Field(description="Уникальный ID фильма")
    title: Annotated[
        str, Field(min_length=1, max_length=255, description="Название фильма")
    ]
    original_title: Annotated[str, Field(max_length=255)] | None = Field(
        default=None, description="Оригинальное название"
    )
    genre: Genre = Field(description="Основной жанр")
    secondary_genres: list[Genre] = Field(default_factory=list, description="Дополнительные жанры")
    release_date: date = Field(description="Дата выхода")
    duration_minutes: PositiveInt = Field(description="Продолжительность в минутах")
    country: Country = Field(description="Страна производства")
    director: Annotated[str, Field(max_length=255, description="Режиссер")]
    description: Annotated[str, Field(max_length=2000)] | None = Field(
        default=None, description="Описание"
    )
    budget_usd: PositiveInt | None = Field(
        default=None, description="Бюджет в долларах"
    )
    is_available: bool = Field(default=True, description="Доступен для просмотра")


class Rating(BaseModel):
    """Модель рейтинга фильма"""

    model_config = ConfigDict(validate_assignment=True)

    rating_id: PositiveInt = Field(description="Уникальный ID рейтинга")
    user_id: UUID = Field(description="UUID пользователя")
    movie_id: PositiveInt = Field(description="ID фильма")
    score: Annotated[float, Field(ge=1.0, le=10.0, description="Оценка от 1 до 10")]
    review_text: Annotated[str, Field(max_length=1000)] | None = Field(
        default=None, description="Текст отзыва"
    )
    created_at: datetime = Field(description="Время создания рейтинга")
    updated_at: datetime | None = Field(default=None, description="Время обновления")


class ViewingSession(BaseModel):
    """Модель сеанса просмотра"""

    model_config = ConfigDict(validate_assignment=True)

    session_id: PositiveInt = Field(description="Уникальный ID сеанса")
    user_id: UUID = Field(description="UUID пользователя")
    movie_id: PositiveInt = Field(description="ID фильма")
    started_at: datetime = Field(description="Время начала просмотра")
    ended_at: datetime | None = Field(
        default=None, description="Время окончания просмотра"
    )
    pause_position_seconds: int = Field(
        default=0, description="Позиция остановки в секундах"
    )
    total_watched_seconds: int = Field(
        default=0, description="Общее время просмотра в секундах"
    )
    device_type: Annotated[str, Field(max_length=50, description="Тип устройства")]
    quality: Annotated[
        str, Field(pattern=r"^(480p|720p|1080p|4K)$", description="Качество видео")
    ]
    is_completed: bool = Field(default=False, description="Завершен ли просмотр")


class UserActivity(BaseModel):
    """Модель активности пользователя"""

    model_config = ConfigDict(validate_assignment=True)

    activity_id: PositiveInt = Field(description="Уникальный ID активности")
    user_id: UUID = Field(description="UUID пользователя")
    activity_type: Annotated[
        str,
        Field(
            pattern=r"^(login|logout|search|play|pause|rate|browse)$",
            description="Тип активности",
        ),
    ]
    activity_data: dict | None = Field(
        default=None, description="Дополнительные данные активности"
    )
    timestamp: datetime = Field(description="Время активности")
    ip_address: (
        Annotated[str, Field(pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")] | None
    ) = Field(default=None, description="IP адрес")
    user_agent: Annotated[str, Field(max_length=500)] | None = Field(
        default=None, description="User Agent"
    )


# Модели для результатов тестирования
class DatabasePerformanceResult(BaseModel):
    """Результат тестирования производительности БД"""

    model_config = ConfigDict(validate_assignment=True)

    database_name: Annotated[
        str, Field(pattern=r"^(clickhouse|vertica)$", description="Название БД")
    ]
    operation: Annotated[str, Field(max_length=100, description="Тип операции")]
    query_description: Annotated[
        str, Field(max_length=255, description="Описание запроса")
    ]
    execution_time_ms: Annotated[
        float, Field(ge=0, description="Время выполнения в миллисекундах")
    ]
    records_processed: int | None = Field(
        default=None, ge=0, description="Количество обработанных записей"
    )
    memory_used_mb: Annotated[float, Field(ge=0)] | None = Field(
        default=None, description="Использованная память в МБ"
    )
    cpu_usage_percent: Annotated[float, Field(ge=0)] | None = Field(
        default=None,
        description="Использование CPU в % (может превышать 100% на многоядерных системах)",
    )
    timestamp: datetime = Field(description="Время выполнения теста")


class BenchmarkConfig(BaseModel):
    """Конфигурация для бенчмарков"""

    model_config = ConfigDict(validate_assignment=True)

    num_users: PositiveInt = Field(
        default=100_000, description="Количество пользователей"
    )
    num_movies: PositiveInt = Field(default=10_000, description="Количество фильмов")
    num_ratings: PositiveInt = Field(
        default=500_000, description="Количество рейтингов"
    )
    num_sessions: PositiveInt = Field(
        default=1_000_000, description="Количество сеансов"
    )
    num_activities: PositiveInt = Field(
        default=2_000_000, description="Количество активностей"
    )
    num_threads: PositiveInt = Field(
        default=10, description="Количество потоков для нагрузочного тестирования"
    )
    queries_per_thread: PositiveInt = Field(
        default=100, description="Количество запросов на поток"
    )
    batch_size: PositiveInt = Field(
        default=10_000, description="Размер батча для вставки"
    )


class TestSuiteResult(BaseModel):
    """Результат полного набора тестов"""

    model_config = ConfigDict(validate_assignment=True)

    # config: BenchmarkConfig = Field(description="Конфигурация тестов")  # Uncomment when BenchmarkConfig is available
    clickhouse_results: list[DatabasePerformanceResult] = Field(
        description="Результаты ClickHouse"
    )
    vertica_results: list[DatabasePerformanceResult] = Field(
        description="Результаты Vertica"
    )
    test_start_time: datetime = Field(description="Время начала тестирования")
    test_end_time: datetime = Field(description="Время окончания тестирования")
    total_duration_seconds: Annotated[
        float, Field(ge=0, description="Общая продолжительность тестов")
    ]

    @property
    def summary(self) -> dict:
        """Создает сводку результатов"""
        clickhouse_avg = (
            sum(r.execution_time_ms for r in self.clickhouse_results)
            / len(self.clickhouse_results)
            if self.clickhouse_results
            else 0
        )
        vertica_avg = (
            sum(r.execution_time_ms for r in self.vertica_results)
            / len(self.vertica_results)
            if self.vertica_results
            else 0
        )

        return {
            "clickhouse_avg_time_ms": round(clickhouse_avg, 2),
            "vertica_avg_time_ms": round(vertica_avg, 2),
            "clickhouse_faster_by": round(
                (vertica_avg - clickhouse_avg) / vertica_avg * 100, 2
            )
            if vertica_avg > 0
            else 0,
            "total_tests": len(self.clickhouse_results) + len(self.vertica_results),
            "duration_minutes": round(self.total_duration_seconds / 60, 2),
        }