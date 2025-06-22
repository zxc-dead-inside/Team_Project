"""
Клиенты для работы с ClickHouse и Vertica
Реализует методы для создания таблиц, вставки данных и выполнения запросов
"""

import json
import time
from contextlib import contextmanager
from typing import Any

import clickhouse_connect
import vertica_python
from loguru import logger
from models import Movie, Rating, User, UserActivity, ViewingSession


class DatabaseClient:
    """Базовый класс для клиентов БД"""

    def __init__(self, connection_params: dict[str, Any]):
        self.connection_params = connection_params
        self.connection = None

    def connect(self):
        """Подключение к БД"""
        raise NotImplementedError

    def disconnect(self):
        """Отключение от БД"""
        raise NotImplementedError

    def execute_query(self, query: str, params: list | None = None) -> Any:
        """Выполнение запроса"""
        raise NotImplementedError

    def create_tables(self):
        """Создание таблиц"""
        raise NotImplementedError

    def drop_tables(self):
        """Удаление таблиц"""
        raise NotImplementedError


class ClickHouseClient(DatabaseClient):
    """Клиент для работы с ClickHouse"""

    def __init__(
        self,
        host: str = "host.docker.internal",
        port: int = 8123,
        database: str = "default",
        username: str = "default",
        password: str = "",
    ):
        super().__init__(
            {
                "host": host,
                "port": port,
                "database": database,
                "username": username,
                "password": password,
            }
        )

    def connect(self):
        """Подключение к ClickHouse"""
        try:
            self.connection = clickhouse_connect.get_client(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                database=self.connection_params["database"],
                username=self.connection_params["username"],
                password=self.connection_params["password"],
            )
            logger.info("Подключение к ClickHouse установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к ClickHouse: {e}")
            raise

    def disconnect(self):
        """Отключение от ClickHouse"""
        if self.connection:
            self.connection.close()
            logger.info("Отключение от ClickHouse")

    def execute_query(self, query: str, params: list | None = None) -> Any:
        """Выполнение запроса в ClickHouse"""
        if not self.connection:
            self.connect()

        try:
            start_time = time.time()
            result = self.connection.query(query, parameters=params or [])
            execution_time = (time.time() - start_time) * 1000
            logger.debug(f"Запрос выполнен за {execution_time:.2f}мс")
            return result.result_rows, execution_time
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса ClickHouse: {e}")
            raise

    def create_tables(self):
        """Создание таблиц в ClickHouse"""
        tables_sql = [
            # Таблица пользователей
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id String,
                email String,
                username String,
                first_name String,
                last_name String,
                country String,
                birth_date Date,
                registration_date DateTime,
                is_premium UInt8
            ) ENGINE = MergeTree()
            ORDER BY user_id
            """,
            # Таблица фильмов
            """
            CREATE TABLE IF NOT EXISTS movies (
                movie_id UInt32,
                title String,
                original_title Nullable(String),
                genre String,
                secondary_genres Array(String),
                release_date Date,
                duration_minutes UInt16,
                country String,
                director String,
                description Nullable(String),
                budget_usd Nullable(UInt64),
                is_available UInt8
            ) ENGINE = MergeTree()
            ORDER BY movie_id
            """,
            # Таблица рейтингов
            """
            CREATE TABLE IF NOT EXISTS ratings (
                rating_id UInt32,
                user_id String,
                movie_id UInt32,
                score Float32,
                review_text Nullable(String),
                created_at DateTime,
                updated_at Nullable(DateTime)
            ) ENGINE = MergeTree()
            ORDER BY (movie_id, user_id)
            """,
            # Таблица сеансов просмотра
            """
            CREATE TABLE IF NOT EXISTS viewing_sessions (
                session_id UInt32,
                user_id String,
                movie_id UInt32,
                started_at DateTime,
                ended_at Nullable(DateTime),
                pause_position_seconds UInt32,
                total_watched_seconds UInt32,
                device_type String,
                quality String,
                is_completed UInt8
            ) ENGINE = MergeTree()
            ORDER BY (user_id, started_at)
            PARTITION BY toYYYYMM(started_at)
            """,
            # Таблица активности пользователей
            """
            CREATE TABLE IF NOT EXISTS user_activities (
                activity_id UInt32,
                user_id String,
                activity_type String,
                activity_data Nullable(String),
                timestamp DateTime,
                ip_address Nullable(String),
                user_agent Nullable(String)
            ) ENGINE = MergeTree()
            ORDER BY (user_id, timestamp)
            PARTITION BY toYYYYMM(timestamp)
            """,
        ]

        for sql in tables_sql:
            self.connection.command(sql)
            logger.info("Таблица создана в ClickHouse")

    def drop_tables(self):
        """Удаление таблиц из ClickHouse"""
        tables = ["users", "movies", "ratings", "viewing_sessions", "user_activities"]
        for table in tables:
            self.connection.command(f"DROP TABLE IF EXISTS {table}")
            logger.info(f"Таблица {table} удалена из ClickHouse")

    def insert_users(self, users: list[User]) -> float:
        """Вставка пользователей"""
        data = []
        for user in users:
            data.append(
                [
                    str(user.user_id),
                    user.email,
                    user.username,
                    user.first_name,
                    user.last_name,
                    user.country.value,
                    user.birth_date,
                    user.registration_date,
                    int(user.is_premium),
                ]
            )

        start_time = time.time()
        self.connection.insert(
            "users",
            data,
            column_names=[
                "user_id",
                "email",
                "username",
                "first_name",
                "last_name",
                "country",
                "birth_date",
                "registration_date",
                "is_premium",
            ],
        )
        return (time.time() - start_time) * 1000

    def insert_movies(self, movies: list[Movie]) -> float:
        """Вставка фильмов"""
        data = []
        for movie in movies:
            data.append(
                [
                    movie.movie_id,
                    movie.title,
                    movie.original_title,
                    movie.genre.value,
                    [g.value for g in movie.secondary_genres],
                    movie.release_date,
                    movie.duration_minutes,
                    movie.country.value,
                    movie.director,
                    movie.description,
                    movie.budget_usd,
                    int(movie.is_available),
                ]
            )

        start_time = time.time()
        self.connection.insert(
            "movies",
            data,
            column_names=[
                "movie_id",
                "title",
                "original_title",
                "genre",
                "secondary_genres",
                "release_date",
                "duration_minutes",
                "country",
                "director",
                "description",
                "budget_usd",
                "is_available",
            ],
        )
        return (time.time() - start_time) * 1000

    def insert_ratings(self, ratings: list[Rating]) -> float:
        """Вставка рейтингов"""
        data = []
        for rating in ratings:
            data.append(
                [
                    rating.rating_id,
                    str(rating.user_id),
                    rating.movie_id,
                    rating.score,
                    rating.review_text,
                    rating.created_at,
                    rating.updated_at,
                ]
            )

        start_time = time.time()
        self.connection.insert(
            "ratings",
            data,
            column_names=[
                "rating_id",
                "user_id",
                "movie_id",
                "score",
                "review_text",
                "created_at",
                "updated_at",
            ],
        )
        return (time.time() - start_time) * 1000

    def insert_viewing_sessions(self, sessions: list[ViewingSession]) -> float:
        """Вставка сеансов просмотра"""
        data = []
        for session in sessions:
            data.append(
                [
                    session.session_id,
                    str(session.user_id),
                    session.movie_id,
                    session.started_at,
                    session.ended_at,
                    session.pause_position_seconds,
                    session.total_watched_seconds,
                    session.device_type,
                    session.quality,
                    int(session.is_completed),
                ]
            )

        start_time = time.time()
        self.connection.insert(
            "viewing_sessions",
            data,
            column_names=[
                "session_id",
                "user_id",
                "movie_id",
                "started_at",
                "ended_at",
                "pause_position_seconds",
                "total_watched_seconds",
                "device_type",
                "quality",
                "is_completed",
            ],
        )
        return (time.time() - start_time) * 1000

    def insert_user_activities(self, activities: list[UserActivity]) -> float:
        """Вставка активностей пользователей"""
        data = []
        for activity in activities:
            activity_data_str = (
                json.dumps(activity.activity_data) if activity.activity_data else None
            )
            data.append(
                [
                    activity.activity_id,
                    str(activity.user_id),
                    activity.activity_type,
                    activity_data_str,
                    activity.timestamp,
                    activity.ip_address,
                    activity.user_agent,
                ]
            )

        start_time = time.time()
        self.connection.insert(
            "user_activities",
            data,
            column_names=[
                "activity_id",
                "user_id",
                "activity_type",
                "activity_data",
                "timestamp",
                "ip_address",
                "user_agent",
            ],
        )
        return (time.time() - start_time) * 1000


class VerticaClient(DatabaseClient):
    """Клиент для работы с Vertica"""

    def __init__(
        self,
        host: str = "host.docker.internal",
        port: int = 5433,
        database: str = "VMart",
        user: str = "dbadmin",
        password: str = "",
    ):
        super().__init__(
            {
                "host": host,
                "port": port,
                "database": database,
                "user": user,
                "password": password,
            }
        )

    def connect(self):
        """Подключение к Vertica"""
        try:
            self.connection = vertica_python.connect(**self.connection_params)
            logger.info("Подключение к Vertica установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к Vertica: {e}")
            raise

    def disconnect(self):
        """Отключение от Vertica"""
        if self.connection:
            self.connection.close()
            logger.info("Отключение от Vertica")

    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для курсора"""
        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def execute_query(self, query: str, params: list | None = None) -> Any:
        """Выполнение запроса в Vertica"""
        if not self.connection:
            self.connect()

        try:
            with self.get_cursor() as cursor:
                start_time = time.time()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                result = cursor.fetchall()
                execution_time = (time.time() - start_time) * 1000
                logger.debug(f"Запрос выполнен за {execution_time:.2f}мс")
                return result, execution_time
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса Vertica: {e}")
            raise

    def create_tables(self):
        """Создание таблиц в Vertica"""
        tables_sql = [
            # Таблица пользователей
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                username VARCHAR(50) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                country VARCHAR(2) NOT NULL,
                birth_date DATE NOT NULL,
                registration_date TIMESTAMP NOT NULL,
                is_premium BOOLEAN DEFAULT FALSE
            )
            """,
            # Таблица фильмов
            """
            CREATE TABLE IF NOT EXISTS movies (
                movie_id INTEGER PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                original_title VARCHAR(255),
                genre VARCHAR(50) NOT NULL,
                secondary_genres VARCHAR(500),
                release_date DATE NOT NULL,
                duration_minutes INTEGER NOT NULL,
                country VARCHAR(2) NOT NULL,
                director VARCHAR(255) NOT NULL,
                description VARCHAR(2000),
                budget_usd BIGINT,
                is_available BOOLEAN DEFAULT TRUE
            )
            """,
            # Таблица рейтингов
            """
            CREATE TABLE IF NOT EXISTS ratings (
                rating_id INTEGER PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                movie_id INTEGER NOT NULL,
                score DECIMAL(3,1) NOT NULL CHECK (score >= 1.0 AND score <= 10.0),
                review_text VARCHAR(1000),
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP
            )
            """,
            # Таблица сеансов просмотра
            """
            CREATE TABLE IF NOT EXISTS viewing_sessions (
                session_id INTEGER PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                movie_id INTEGER NOT NULL,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                pause_position_seconds INTEGER DEFAULT 0,
                total_watched_seconds INTEGER DEFAULT 0,
                device_type VARCHAR(50) NOT NULL,
                quality VARCHAR(10) NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE
            )
            """,
            # Таблица активности пользователей
            """
            CREATE TABLE IF NOT EXISTS user_activities (
                activity_id INTEGER PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                activity_type VARCHAR(20) NOT NULL,
                activity_data VARCHAR(1000),
                timestamp TIMESTAMP NOT NULL,
                ip_address VARCHAR(15),
                user_agent VARCHAR(500)
            )
            """,
        ]

        with self.get_cursor() as cursor:
            for sql in tables_sql:
                cursor.execute(sql)
                logger.info("Таблица создана в Vertica")
            self.connection.commit()

    def drop_tables(self):
        """Удаление таблиц из Vertica"""
        tables = ["users", "movies", "ratings", "viewing_sessions", "user_activities"]

        with self.get_cursor() as cursor:
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                logger.info(f"Таблица {table} удалена из Vertica")
            self.connection.commit()

    def insert_users(self, users: list[User]) -> float:
        """Вставка пользователей"""
        sql = """
        INSERT INTO users 
        (user_id, email, username, first_name, last_name, country, 
         birth_date, registration_date, is_premium)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        data = []
        for user in users:
            data.append(
                (
                    str(user.user_id),
                    user.email,
                    user.username,
                    user.first_name,
                    user.last_name,
                    user.country.value,
                    user.birth_date,
                    user.registration_date,
                    user.is_premium,
                )
            )

        start_time = time.time()
        with self.get_cursor() as cursor:
            cursor.executemany(sql, data)
            self.connection.commit()
        return (time.time() - start_time) * 1000

    def insert_movies(self, movies: list[Movie]) -> float:
        """Вставка фильмов"""
        sql = """
        INSERT INTO movies 
        (movie_id, title, original_title, genre, secondary_genres, release_date,
         duration_minutes, country, director, description, budget_usd, is_available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        data = []
        for movie in movies:
            secondary_genres_str = (
                ",".join([g.value for g in movie.secondary_genres])
                if movie.secondary_genres
                else None
            )
            data.append(
                (
                    movie.movie_id,
                    movie.title,
                    movie.original_title,
                    movie.genre.value,
                    secondary_genres_str,
                    movie.release_date,
                    movie.duration_minutes,
                    movie.country.value,
                    movie.director,
                    movie.description,
                    movie.budget_usd,
                    movie.is_available,
                )
            )

        start_time = time.time()
        with self.get_cursor() as cursor:
            cursor.executemany(sql, data)
            self.connection.commit()
        return (time.time() - start_time) * 1000

    def insert_ratings(self, ratings: list[Rating]) -> float:
        """Вставка рейтингов"""
        sql = """
        INSERT INTO ratings 
        (rating_id, user_id, movie_id, score, review_text, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        data = []
        for rating in ratings:
            data.append(
                (
                    rating.rating_id,
                    str(rating.user_id),
                    rating.movie_id,
                    rating.score,
                    rating.review_text,
                    rating.created_at,
                    rating.updated_at,
                )
            )

        start_time = time.time()
        with self.get_cursor() as cursor:
            cursor.executemany(sql, data)
            self.connection.commit()
        return (time.time() - start_time) * 1000

    def insert_viewing_sessions(self, sessions: list[ViewingSession]) -> float:
        """Вставка сеансов просмотра"""
        sql = """
        INSERT INTO viewing_sessions 
        (session_id, user_id, movie_id, started_at, ended_at, pause_position_seconds,
         total_watched_seconds, device_type, quality, is_completed)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        data = []
        for session in sessions:
            data.append(
                (
                    session.session_id,
                    str(session.user_id),
                    session.movie_id,
                    session.started_at,
                    session.ended_at,
                    session.pause_position_seconds,
                    session.total_watched_seconds,
                    session.device_type,
                    session.quality,
                    session.is_completed,
                )
            )

        start_time = time.time()
        with self.get_cursor() as cursor:
            cursor.executemany(sql, data)
            self.connection.commit()
        return (time.time() - start_time) * 1000

    def insert_user_activities(self, activities: list[UserActivity]) -> float:
        """Вставка активностей пользователей"""
        sql = (
            "INSERT INTO user_activities ("
            "activity_id, user_id, activity_type, activity_data, "
            "timestamp, ip_address, user_agent"
            ") VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )

        data = []
        for activity in activities:
            activity_data_str = (
                json.dumps(activity.activity_data) if activity.activity_data else None
            )
            data.append(
                (
                    activity.activity_id,
                    str(activity.user_id),
                    activity.activity_type,
                    activity_data_str,
                    activity.timestamp,
                    activity.ip_address,
                    activity.user_agent,
                )
            )

        start_time = time.time()
        with self.get_cursor() as cursor:
            cursor.executemany(sql, data)
            self.connection.commit()
        return (time.time() - start_time) * 1000
