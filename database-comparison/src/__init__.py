"""
Пакет для исследования производительности ClickHouse vs Vertica
в контексте онлайн-кинотеатра
"""

__version__ = "1.0.0"
__author__ = "Performance Research Team"
__description__ = (
    "Сравнение производительности ClickHouse и Vertica для онлайн-кинотеатра"
)

# Основные модули
from .benchmark import DatabaseBenchmark
from .data_generator import CinemaDataGenerator
from .database_clients import ClickHouseClient, VerticaClient
from .models import (
    BenchmarkConfig,
    Country,
    DatabasePerformanceResult,
    Genre,
    Movie,
    Rating,
    TestSuiteResult,
    User,
    UserActivity,
    ViewingSession,
)


__all__ = [
    # Модели данных
    "User",
    "Movie",
    "Rating",
    "ViewingSession",
    "UserActivity",
    "BenchmarkConfig",
    "DatabasePerformanceResult",
    "TestSuiteResult",
    "Genre",
    "Country",
    # Основные классы
    "CinemaDataGenerator",
    "ClickHouseClient",
    "VerticaClient",
    "DatabaseBenchmark",
]
