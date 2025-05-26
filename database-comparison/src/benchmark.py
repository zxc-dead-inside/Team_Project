"""
Модуль для тестирования производительности ClickHouse vs Vertica
Содержит агрегационные запросы и многопоточное тестирование
"""

import concurrent.futures
import time
from datetime import datetime
from statistics import mean, median, stdev
from typing import Any

import psutil
from database_clients import ClickHouseClient, VerticaClient
from loguru import logger
from models import DatabasePerformanceResult
from tqdm import tqdm


class DatabaseBenchmark:
    """Класс для тестирования производительности БД"""

    def __init__(
        self, clickhouse_client: ClickHouseClient, vertica_client: VerticaClient
    ):
        self.clickhouse = clickhouse_client
        self.vertica = vertica_client
        self.results: list[DatabasePerformanceResult] = []

    def get_analytical_queries(self) -> dict[str, tuple[str, str]]:
        """
        Возвращает набор аналитических запросов для тестирования

        Returns:
            Dict: Словарь с описанием и парами запросов (ClickHouse, Vertica)
        """
        queries = {
            "Топ-10 популярных фильмов по количеству просмотров": (
                """
                SELECT 
                    m.title,
                    m.genre,
                    COUNT(*) as view_count,
                    AVG(r.score) as avg_rating
                FROM viewing_sessions vs
                JOIN movies m ON vs.movie_id = m.movie_id
                LEFT JOIN ratings r ON m.movie_id = r.movie_id
                WHERE vs.is_completed = 1
                GROUP BY m.movie_id, m.title, m.genre
                ORDER BY view_count DESC
                LIMIT 10
                """,
                """
                SELECT 
                    m.title,
                    m.genre,
                    COUNT(*) as view_count,
                    AVG(r.score) as avg_rating
                FROM viewing_sessions vs
                JOIN movies m ON vs.movie_id = m.movie_id
                LEFT JOIN ratings r ON m.movie_id = r.movie_id
                WHERE vs.is_completed = true
                GROUP BY m.movie_id, m.title, m.genre
                ORDER BY view_count DESC
                LIMIT 10
                """,
            ),
            "Средний рейтинг фильмов по жанрам": (
                """
                SELECT 
                    genre,
                    COUNT(*) as movie_count,
                    AVG(avg_rating) as avg_genre_rating,
                    MIN(avg_rating) as min_rating,
                    MAX(avg_rating) as max_rating
                FROM (
                    SELECT 
                        m.genre,
                        m.movie_id,
                        AVG(r.score) as avg_rating
                    FROM movies m
                    LEFT JOIN ratings r ON m.movie_id = r.movie_id
                    WHERE r.score IS NOT NULL
                    GROUP BY m.genre, m.movie_id
                ) as movie_ratings
                GROUP BY genre
                ORDER BY avg_genre_rating DESC
                """,
                """
                SELECT 
                    genre,
                    COUNT(*) as movie_count,
                    AVG(avg_rating) as avg_genre_rating,
                    MIN(avg_rating) as min_rating,
                    MAX(avg_rating) as max_rating
                FROM (
                    SELECT 
                        m.genre,
                        m.movie_id,
                        AVG(r.score) as avg_rating
                    FROM movies m
                    LEFT JOIN ratings r ON m.movie_id = r.movie_id
                    WHERE r.score IS NOT NULL
                    GROUP BY m.genre, m.movie_id
                ) as movie_ratings
                GROUP BY genre
                ORDER BY avg_genre_rating DESC
                """,
            ),
            "Активность пользователей за последний месяц": (
                """
                SELECT 
                    u.country,
                    COUNT(DISTINCT ua.user_id) as active_users,
                    COUNT(*) as total_activities,
                    COUNT(*) / COUNT(DISTINCT ua.user_id) as avg_activities_per_user
                FROM user_activities ua
                JOIN users u ON ua.user_id = u.user_id
                WHERE ua.timestamp >= subtractMonths(now(), 1)
                GROUP BY u.country
                ORDER BY active_users DESC
                """,
                """
                SELECT 
                    u.country,
                    COUNT(DISTINCT ua.user_id) as active_users,
                    COUNT(*) as total_activities,
                    COUNT(*) / COUNT(DISTINCT ua.user_id) as avg_activities_per_user
                FROM user_activities ua
                JOIN users u ON ua.user_id = u.user_id
                WHERE ua.timestamp >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY u.country
                ORDER BY active_users DESC
                """,
            ),
            "Статистика просмотров по устройствам и качеству": (
                """
                SELECT 
                    device_type,
                    quality,
                    COUNT(*) as session_count,
                    AVG(total_watched_seconds) as avg_watch_time,
                    SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_sessions,
                    SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as completion_rate
                FROM viewing_sessions
                GROUP BY device_type, quality
                ORDER BY session_count DESC
                """,
                """
                SELECT 
                    device_type,
                    quality,
                    COUNT(*) as session_count,
                    AVG(total_watched_seconds) as avg_watch_time,
                    SUM(CASE WHEN is_completed = true THEN 1 ELSE 0 END) as completed_sessions,
                    SUM(CASE WHEN is_completed = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as completion_rate
                FROM viewing_sessions
                GROUP BY device_type, quality
                ORDER BY session_count DESC
                """,
            ),
            "Топ пользователей по времени просмотра": (
                """
                SELECT 
                    u.username,
                    u.country,
                    u.is_premium,
                    SUM(vs.total_watched_seconds) as total_watch_time,
                    COUNT(DISTINCT vs.movie_id) as unique_movies_watched,
                    COUNT(*) as total_sessions
                FROM viewing_sessions vs
                JOIN users u ON vs.user_id = u.user_id
                GROUP BY u.user_id, u.username, u.country, u.is_premium
                ORDER BY total_watch_time DESC
                LIMIT 100
                """,
                """
                SELECT 
                    u.username,
                    u.country,
                    u.is_premium,
                    SUM(vs.total_watched_seconds) as total_watch_time,
                    COUNT(DISTINCT vs.movie_id) as unique_movies_watched,
                    COUNT(*) as total_sessions
                FROM viewing_sessions vs
                JOIN users u ON vs.user_id = u.user_id
                GROUP BY u.user_id, u.username, u.country, u.is_premium
                ORDER BY total_watch_time DESC
                LIMIT 100
                """,
            ),
            "Анализ рейтингов по возрастным группам": (
                """
                SELECT 
                    CASE 
                        WHEN age < 25 THEN '18-24'
                        WHEN age < 35 THEN '25-34'
                        WHEN age < 45 THEN '35-44'
                        WHEN age < 55 THEN '45-54'
                        ELSE '55+'
                    END as age_group,
                    m.genre,
                    AVG(r.score) as avg_rating,
                    COUNT(*) as rating_count
                FROM ratings r
                JOIN users u ON r.user_id = u.user_id
                JOIN movies m ON r.movie_id = m.movie_id
                JOIN (SELECT 
                    user_id, 
                    dateDiff('year', birth_date, today()) as age 
                 FROM users
                ) as user_ages ON r.user_id = user_ages.user_id
                GROUP BY age_group, m.genre
                ORDER BY age_group, avg_rating DESC
                """,
                """
                SELECT 
                    CASE 
                        WHEN EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM u.birth_date) < 25 THEN '18-24'
                        WHEN EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM u.birth_date) < 35 THEN '25-34'
                        WHEN EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM u.birth_date) < 45 THEN '35-44'
                        WHEN EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM u.birth_date) < 55 THEN '45-54'
                        ELSE '55+'
                    END as age_group,
                    m.genre,
                    AVG(r.score) as avg_rating,
                    COUNT(*) as rating_count
                FROM ratings r
                JOIN users u ON r.user_id = u.user_id
                JOIN movies m ON r.movie_id = m.movie_id
                GROUP BY age_group, m.genre
                ORDER BY age_group, avg_rating DESC
                """,
            ),
            "Тренды просмотров по месяцам": (
                """
                SELECT 
                    toYYYYMM(started_at) as month,
                    COUNT(*) as total_sessions,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(total_watched_seconds) as avg_session_duration,
                    SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_sessions
                FROM viewing_sessions
                WHERE started_at >= subtractMonths(now(), 12)
                GROUP BY month
                ORDER BY month
                """,
                """
                SELECT 
                    EXTRACT(YEAR FROM started_at) * 100 + EXTRACT(MONTH FROM started_at) as month,
                    COUNT(*) as total_sessions,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(total_watched_seconds) as avg_session_duration,
                    SUM(CASE WHEN is_completed = true THEN 1 ELSE 0 END) as completed_sessions
                FROM viewing_sessions
                WHERE started_at >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY EXTRACT(YEAR FROM started_at), EXTRACT(MONTH FROM started_at)
                ORDER BY month
                """,
            ),
        }

        return queries

    def measure_performance(
        self, database_name: str, client, query: str, description: str
    ) -> DatabasePerformanceResult:
        """
        Измеряет производительность выполнения запроса

        Args:
            database_name: Название БД
            client: Клиент БД
            query: SQL запрос
            description: Описание запроса

        Returns:
            DatabasePerformanceResult: Результат измерения
        """
        # Измерение использования ресурсов до выполнения
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Инициализация CPU мониторинга
        process.cpu_percent()  # Первый вызов для инициализации
        time.sleep(0.1)  # Небольшая пауза для корректного измерения

        try:
            # Выполнение запроса
            result, execution_time = client.execute_query(query)
            records_processed = len(result) if result else 0

            # Измерение использования ресурсов после выполнения
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            cpu_usage = process.cpu_percent()  # CPU за период выполнения запроса

            # Ограничиваем CPU usage разумными пределами (максимум 800% для 8-ядерной системы)
            if cpu_usage > 800:
                cpu_usage = min(cpu_usage, 800)

            memory_used = max(0, memory_after - memory_before)

            return DatabasePerformanceResult(
                database_name=database_name,
                operation="analytical_query",
                query_description=description,
                execution_time_ms=execution_time,
                records_processed=records_processed,
                memory_used_mb=memory_used,
                cpu_usage_percent=cpu_usage,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Ошибка выполнения запроса в {database_name}: {e}")
            # Возвращаем результат с ошибкой
            return DatabasePerformanceResult(
                database_name=database_name,
                operation="analytical_query",
                query_description=f"{description} (ОШИБКА)",
                execution_time_ms=999999.0,
                records_processed=None,  # None вместо 0
                memory_used_mb=None,
                cpu_usage_percent=None,
                timestamp=datetime.now(),
            )

    def run_analytical_queries(self) -> list[DatabasePerformanceResult]:
        """
        Выполняет все аналитические запросы для обеих БД

        Returns:
            List[DatabasePerformanceResult]: Результаты тестов
        """
        results = []
        queries = self.get_analytical_queries()

        logger.info("Начало выполнения аналитических запросов")

        for description, (clickhouse_query, vertica_query) in tqdm(
            queries.items(), desc="Выполнение запросов"
        ):
            # Тест ClickHouse
            logger.info(f"Тестирование ClickHouse: {description}")
            ch_result = self.measure_performance(
                "clickhouse", self.clickhouse, clickhouse_query, description
            )
            results.append(ch_result)

            # Небольшая пауза между запросами
            time.sleep(1)

            # Тест Vertica
            logger.info(f"Тестирование Vertica: {description}")
            vertica_result = self.measure_performance(
                "vertica", self.vertica, vertica_query, description
            )
            results.append(vertica_result)

            # Пауза между разными типами запросов
            time.sleep(2)

        logger.info("Аналитические запросы завершены")
        return results

    def worker_function(
        self,
        database_name: str,
        client_class,
        queries: list[tuple[str, str]],
        thread_id: int,
        queries_per_thread: int,
    ) -> list[DatabasePerformanceResult]:
        """
        Функция для выполнения запросов в отдельном потоке

        Args:
            database_name: Название БД
            client_class: Класс клиента БД
            queries: Список запросов
            thread_id: ID потока
            queries_per_thread: Количество запросов на поток

        Returns:
            List[DatabasePerformanceResult]: Результаты выполнения
        """
        thread_results = []

        # Создаем отдельный клиент для этого потока
        thread_client = client_class()
        thread_client.connect()

        try:
            for i in range(queries_per_thread):
                # Выбираем случайный запрос
                query_desc, query = queries[i % len(queries)]

                result = self.measure_performance(
                    database_name=database_name,
                    client=thread_client,
                    query=query,
                    description=f"{query_desc} (поток {thread_id}, запрос {i + 1})",
                )
                thread_results.append(result)

                # Небольшая пауза между запросами
                time.sleep(0.1)
        finally:
            # Закрываем соединение потока
            thread_client.disconnect()

        return thread_results

    def run_concurrent_test(
        self, num_threads: int = 10, queries_per_thread: int = 100
    ) -> list[DatabasePerformanceResult]:
        """
        Выполняет многопоточное тестирование

        Args:
            num_threads: Количество потоков
            queries_per_thread: Количество запросов на поток

        Returns:
            List[DatabasePerformanceResult]: Результаты тестов
        """
        results = []

        # Подготавливаем упрощенные запросы для нагрузочного тестирования
        simple_queries = [
            (
                "Подсчет пользователей",
                "SELECT COUNT(*) FROM users",
                "SELECT COUNT(*) FROM users",
            ),
            (
                "Подсчет фильмов",
                "SELECT COUNT(*) FROM movies",
                "SELECT COUNT(*) FROM movies",
            ),
            (
                "Средний рейтинг",
                "SELECT AVG(score) FROM ratings",
                "SELECT AVG(score) FROM ratings",
            ),
            (
                "Количество сеансов",
                "SELECT COUNT(*) FROM viewing_sessions",
                "SELECT COUNT(*) FROM viewing_sessions",
            ),
        ]

        logger.info(
            f"Начало многопоточного тестирования: {num_threads} потоков, {queries_per_thread} запросов на поток"
        )

        # Тестирование ClickHouse
        logger.info("Многопоточное тестирование ClickHouse")
        clickhouse_queries = [(desc, ch_query) for desc, ch_query, _ in simple_queries]

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for thread_id in range(num_threads):
                future = executor.submit(
                    self.worker_function,
                    "clickhouse",
                    type(self.clickhouse),  # Передаем класс клиента
                    clickhouse_queries,
                    thread_id,
                    queries_per_thread,
                )
                futures.append(future)

            # Собираем результаты
            for future in concurrent.futures.as_completed(futures):
                thread_results = future.result()
                results.extend(thread_results)

        # Пауза между тестами
        time.sleep(5)

        # Тестирование Vertica
        logger.info("Многопоточное тестирование Vertica")
        vertica_queries = [(desc, v_query) for desc, _, v_query in simple_queries]

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for thread_id in range(num_threads):
                future = executor.submit(
                    self.worker_function,
                    "vertica",
                    type(self.vertica),  # Передаем класс клиента
                    vertica_queries,
                    thread_id,
                    queries_per_thread,
                )
                futures.append(future)

            # Собираем результаты
            for future in concurrent.futures.as_completed(futures):
                thread_results = future.result()
                results.extend(thread_results)

        logger.info("Многопоточное тестирование завершено")
        return results

    def analyze_results(
        self, results: list[DatabasePerformanceResult]
    ) -> dict[str, Any]:
        """
        Анализирует результаты тестирования

        Args:
            results: Результаты тестов

        Returns:
            Dict: Анализ результатов
        """
        clickhouse_results = [r for r in results if r.database_name == "clickhouse"]
        vertica_results = [r for r in results if r.database_name == "vertica"]

        analysis = {
            "summary": {
                "total_tests": len(results),
                "clickhouse_tests": len(clickhouse_results),
                "vertica_tests": len(vertica_results),
            },
            "clickhouse": self._analyze_database_results(clickhouse_results),
            "vertica": self._analyze_database_results(vertica_results),
            "comparison": {},
        }

        # Сравнение производительности
        if clickhouse_results and vertica_results:
            ch_successful = [
                r for r in clickhouse_results if r.execution_time_ms < 999999
            ]
            v_successful = [r for r in vertica_results if r.execution_time_ms < 999999]

            if ch_successful and v_successful:
                ch_avg_time = mean([r.execution_time_ms for r in ch_successful])
                v_avg_time = mean([r.execution_time_ms for r in v_successful])

                analysis["comparison"] = {
                    "clickhouse_avg_time_ms": round(ch_avg_time, 2),
                    "vertica_avg_time_ms": round(v_avg_time, 2),
                    "clickhouse_faster_percent": round(
                        (v_avg_time - ch_avg_time) / v_avg_time * 100, 2
                    )
                    if v_avg_time > 0
                    else 0,
                    "performance_winner": "ClickHouse"
                    if ch_avg_time < v_avg_time
                    else "Vertica",
                }

        return analysis

    def _analyze_database_results(
        self, results: list[DatabasePerformanceResult]
    ) -> dict[str, Any]:
        """Анализирует результаты для одной БД"""
        if not results:
            return {}

        execution_times = [
            r.execution_time_ms for r in results if r.execution_time_ms < 999999
        ]

        if not execution_times:
            return {"error": "Нет успешных запросов"}

        return {
            "total_queries": len(results),
            "successful_queries": len(execution_times),
            "failed_queries": len(results) - len(execution_times),
            "success_rate_percent": round(
                (len(execution_times) / len(results)) * 100, 2
            ),
            "avg_execution_time_ms": round(mean(execution_times), 2),
            "median_execution_time_ms": round(median(execution_times), 2),
            "min_execution_time_ms": round(min(execution_times), 2),
            "max_execution_time_ms": round(max(execution_times), 2),
            "std_execution_time_ms": round(stdev(execution_times), 2)
            if len(execution_times) > 1
            else 0,
            "total_records_processed": sum([r.records_processed or 0 for r in results]),
            "avg_memory_used_mb": round(
                mean([r.memory_used_mb or 0 for r in results]), 2
            ),
            "avg_cpu_usage_percent": round(
                mean([r.cpu_usage_percent or 0 for r in results]), 2
            ),
        }

    def save_results_to_file(
        self,
        results: list[DatabasePerformanceResult],
        filename: str = "benchmark_results.json",
    ) -> None:
        """
        Сохраняет результаты в файл

        Args:
            results: Результаты тестирования
            filename: Имя файла для сохранения
        """
        import json

        serializable_results = []
        for result in results:
            serializable_results.append(
                {
                    "database_name": result.database_name,
                    "operation": result.operation,
                    "query_description": result.query_description,
                    "execution_time_ms": result.execution_time_ms,
                    "records_processed": result.records_processed,
                    "memory_used_mb": result.memory_used_mb,
                    "cpu_usage_percent": result.cpu_usage_percent,
                    "timestamp": result.timestamp.isoformat()
                    if result.timestamp
                    else None,
                }
            )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)

        logger.info(f"Результаты сохранены в файл: {filename}")

    def run_full_benchmark(
        self,
        save_results: bool = True,
        concurrent_threads: int = 5,
        concurrent_queries_per_thread: int = 50,
    ) -> dict[str, Any]:
        """
        Запускает полное тестирование производительности

        Args:
            save_results: Сохранять ли результаты в файл
            concurrent_threads: Количество потоков для нагрузочного тестирования
            concurrent_queries_per_thread: Количество запросов на поток

        Returns:
            Dict: Полный анализ результатов
        """
        logger.info("Начало полного тестирования производительности")

        # Аналитические запросы
        analytical_results = self.run_analytical_queries()

        # Многопоточное тестирование
        concurrent_results = self.run_concurrent_test(
            num_threads=concurrent_threads,
            queries_per_thread=concurrent_queries_per_thread,
        )

        # Объединяем все результаты
        all_results = analytical_results + concurrent_results

        # Анализируем результаты
        analysis = self.analyze_results(all_results)
        analysis["test_config"] = {
            "concurrent_threads": concurrent_threads,
            "concurrent_queries_per_thread": concurrent_queries_per_thread,
            "total_analytical_queries": len(self.get_analytical_queries())
            * 2,  # для 2х БД
            "total_concurrent_queries": concurrent_threads
            * concurrent_queries_per_thread
            * 2,  # для 2х БД
        }

        if save_results:
            self.save_results_to_file(all_results)

        logger.info("Полное тестирование производительности завершено")
        return analysis
