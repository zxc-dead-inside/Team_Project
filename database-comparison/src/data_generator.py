"""
Генератор тестовых данных для онлайн-кинотеатра
Создает реалистичные данные для тестирования производительности БД
"""

import random
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from itertools import islice
from uuid import UUID, uuid4

import numpy as np
from faker import Faker
from models import (
    BenchmarkConfig,
    Country,
    Genre,
    Movie,
    Rating,
    User,
    UserActivity,
    ViewingSession,
)


class CinemaDataGenerator:
    """Генератор данных для онлайн-кинотеатра"""

    def __init__(self, seed: int = 42):
        """
        Инициализация генератора

        Args:
            seed: Семя для воспроизводимости результатов
        """
        self.fake = Faker(["ru_RU", "en_US"], seed=seed)
        random.seed(seed)
        np.random.seed(seed)

        # Счетчики для уникальных ID
        self._movie_id_counter = 0
        self._rating_id_counter = 0
        self._session_id_counter = 0
        self._activity_id_counter = 0

        # Список сгенерированных user_id для использования в foreign keys
        self._generated_user_ids: list[UUID] = []

        # Настройка весов для более реалистичного распределения
        self.genre_weights = {
            Genre.ACTION: 0.15,
            Genre.COMEDY: 0.18,
            Genre.DRAMA: 0.20,
            Genre.HORROR: 0.08,
            Genre.ROMANCE: 0.12,
            Genre.THRILLER: 0.10,
            Genre.DOCUMENTARY: 0.05,
            Genre.ANIMATION: 0.07,
            Genre.FANTASY: 0.08,
            Genre.SCIENCE_FICTION: 0.07,
        }

        self.country_weights = {
            Country.US: 0.35,
            Country.RU: 0.20,
            Country.UK: 0.10,
            Country.DE: 0.08,
            Country.FR: 0.08,
            Country.IT: 0.05,
            Country.ES: 0.04,
            Country.JP: 0.04,
            Country.KR: 0.03,
            Country.CN: 0.03,
        }

        # Популярные названия фильмов по жанрам для реалистичности
        self.movie_titles_by_genre = {
            Genre.ACTION: [
                "Скорость",
                "Штурм",
                "Операция",
                "Миссия",
                "Побег",
                "Удар",
                "Война",
                "Битва",
                "Охота",
                "Погоня",
                "Взрыв",
                "Атака",
                "Рейд",
                "Код",
                "Цель",
            ],
            Genre.COMEDY: [
                "Смех",
                "Веселье",
                "Шутка",
                "Комедия",
                "Юмор",
                "Приключения",
                "Путешествие",
                "Каникулы",
                "Встреча",
                "Свадьба",
                "Праздник",
                "Сюрприз",
                "Забава",
            ],
            Genre.DRAMA: [
                "Жизнь",
                "Судьба",
                "История",
                "Семья",
                "Любовь",
                "Потеря",
                "Выбор",
                "Путь",
                "Мечта",
                "Надежда",
                "Прошлое",
                "Будущее",
                "Память",
                "Сердце",
            ],
            Genre.HORROR: [
                "Кошмар",
                "Ужас",
                "Тьма",
                "Страх",
                "Призрак",
                "Дом",
                "Ночь",
                "Тень",
                "Проклятие",
                "Зло",
                "Мертвые",
                "Крик",
                "Безумие",
                "Демон",
            ],
        }

    def _weighted_choice(self, choices: dict) -> any:
        """Выбор элемента с учетом весов"""
        items = list(choices.keys())
        weights = list(choices.values())
        # Используем random.choices для корректной работы с enum
        return random.choices(items, weights=weights, k=1)[0]

    def _get_random_user_id(self) -> UUID:
        """Возвращает случайный UUID пользователя из уже сгенерированных"""
        if not self._generated_user_ids:
            raise ValueError("Нет сгенерированных пользователей для выбора user_id")
        return random.choice(self._generated_user_ids)

    def generate_users(self, count: int) -> Iterator[User]:
        """
        Генерирует пользователей

        Args:
            count: Количество пользователей

        Yields:
            User: Объект пользователя
        """
        # Очищаем список при новой генерации
        self._generated_user_ids.clear()
        
        for _ in range(count):
            # Генерируем новый UUID для каждого пользователя
            user_id = uuid4()
            self._generated_user_ids.append(user_id)

            # Генерация основных данных
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            username = (
                f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
            )
            email = f"{username}@{self.fake.domain_name()}"

            # Дата рождения (очень консервативный диапазон для ClickHouse)
            birth_date = self.fake.date_between(
                start_date=date(1970, 1, 1),  # С 1970 года
                end_date=date(2010, 1, 1),  # До 2010 года (14+ лет)
            )

            # Дата регистрации (консервативный диапазон)
            registration_date = self.fake.date_time_between(
                start_date=datetime(2020, 1, 1),  # С 2020 года
                end_date=datetime(2023, 12, 31),  # До конца 2023
            )

            # Премиум подписка у 20% пользователей
            is_premium = random.random() < 0.2

            country = self._weighted_choice(self.country_weights)

            yield User(
                user_id=user_id,
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                country=country,
                birth_date=birth_date,
                registration_date=registration_date,
                is_premium=is_premium,
            )

    def generate_movies(self, count: int) -> Iterator[Movie]:
        """
        Генерирует фильмы

        Args:
            count: Количество фильмов

        Yields:
            Movie: Объект фильма
        """
        directors = [
            self.fake.name() for _ in range(count // 10)
        ]  # 10% уникальных режиссеров

        for _ in range(count):
            self._movie_id_counter += 1
            movie_id = self._movie_id_counter
            genre = self._weighted_choice(self.genre_weights)
            country = self._weighted_choice(self.country_weights)

            # Генерация названия в зависимости от жанра
            if genre in self.movie_titles_by_genre:
                base_title = random.choice(self.movie_titles_by_genre[genre])
                number = random.randint(1, 100) if random.random() < 0.3 else ""
                title = f"{base_title}{f' {number}' if number else ''}"
            else:
                title = self.fake.catch_phrase()

            # Оригинальное название для зарубежных фильмов
            original_title = self.fake.catch_phrase() if country != Country.RU else None

            # Дополнительные жанры (0-2)
            secondary_genres = []
            if random.random() < 0.4:  # 40% фильмов имеют дополнительные жанры
                available_genres = [g for g in Genre if g != genre]
                secondary_genres = random.sample(available_genres, random.randint(1, 2))

            # Дата выхода (очень консервативный диапазон для ClickHouse)
            release_date = self.fake.date_between(
                start_date=date(1995, 1, 1),  # С 1995 года
                end_date=date(2023, 12, 31),  # До конца 2023
            )

            # Продолжительность в зависимости от жанра
            if genre == Genre.DOCUMENTARY:
                duration = random.randint(45, 180)
            elif genre == Genre.ANIMATION:
                duration = random.randint(80, 120)
            else:
                duration = random.randint(90, 180)

            # Бюджет для части фильмов
            budget = None
            if random.random() < 0.6:  # У 60% фильмов указан бюджет
                budget = random.randint(100_000, 200_000_000)

            # 95% фильмов доступны
            is_available = random.random() < 0.95

            yield Movie(
                movie_id=movie_id,
                title=title,
                original_title=original_title,
                genre=genre,
                secondary_genres=secondary_genres,
                release_date=release_date,
                duration_minutes=duration,
                country=country,
                director=random.choice(directors),
                description=self.fake.text(max_nb_chars=500)
                if random.random() < 0.8
                else None,
                budget_usd=budget,
                is_available=is_available,
            )

    def generate_ratings(
        self, count: int, user_count: int, movie_count: int
    ) -> Iterator[Rating]:
        """
        Генерирует рейтинги фильмов

        Args:
            count: Количество рейтингов
            user_count: Общее количество пользователей (используем сгенерированные UUIDs)
            movie_count: Общее количество фильмов

        Yields:
            Rating: Объект рейтинга
        """
        if not self._generated_user_ids:
            raise ValueError("Необходимо сначала сгенерировать пользователей перед генерацией рейтингов")

        # Распределение оценок (больше высоких оценок)
        score_distribution = [1, 1, 2, 3, 5, 8, 12, 15, 20, 33]  # Веса для оценок 1-10

        for _ in range(count):
            self._rating_id_counter += 1
            rating_id = self._rating_id_counter

            user_id = self._get_random_user_id()
            movie_id = random.randint(1, movie_count)

            # Генерация оценки с учетом распределения
            score_choice = random.choices(
                range(1, 11), weights=score_distribution, k=1
            )[0]
            score = float(score_choice)

            # Отзыв для части оценок
            review_text = None
            if random.random() < 0.3:  # 30% оценок с отзывами
                review_text = self.fake.text(max_nb_chars=300)

            created_at = self.fake.date_time_between(
                start_date=datetime(2021, 1, 1),  # С 2021 года
                end_date=datetime(2023, 12, 31),  # До конца 2023
            )

            # Некоторые отзывы обновлялись
            updated_at = None
            if review_text and random.random() < 0.1:  # 10% отзывов обновлялись
                updated_at = self.fake.date_time_between(
                    start_date=created_at, end_date=datetime(2023, 12, 31)
                )

            yield Rating(
                rating_id=rating_id,
                user_id=user_id,
                movie_id=movie_id,
                score=score,
                review_text=review_text,
                created_at=created_at,
                updated_at=updated_at,
            )

    def generate_viewing_sessions(
        self, count: int, user_count: int, movie_count: int
    ) -> Iterator[ViewingSession]:
        """
        Генерирует сеансы просмотра

        Args:
            count: Количество сеансов
            user_count: Общее количество пользователей (используем сгенерированные UUIDs)
            movie_count: Общее количество фильмов

        Yields:
            ViewingSession: Объект сеанса просмотра
        """
        if not self._generated_user_ids:
            raise ValueError("Необходимо сначала сгенерировать пользователей перед генерацией сеансов просмотра")

        device_types = ["mobile", "desktop", "smart_tv", "tablet"]
        device_weights = [0.4, 0.3, 0.2, 0.1]

        qualities = ["480p", "720p", "1080p", "4K"]
        quality_weights = [0.1, 0.3, 0.5, 0.1]

        for _ in range(count):
            self._session_id_counter += 1
            session_id = self._session_id_counter

            user_id = self._get_random_user_id()
            movie_id = random.randint(1, movie_count)

            started_at = self.fake.date_time_between(
                start_date=datetime(2021, 1, 1),  # С 2021 года
                end_date=datetime(2023, 12, 31),  # До конца 2023
            )

            # Предполагаем среднюю длительность фильма 120 минут
            movie_duration = random.randint(90, 180) * 60  # в секундах

            # 70% сеансов завершены
            is_completed = random.random() < 0.7

            if is_completed:
                total_watched = movie_duration
                pause_position = 0
                ended_at = started_at + timedelta(
                    seconds=movie_duration + random.randint(0, 300)
                )
            else:
                # Для незавершенных - случайная позиция
                total_watched = random.randint(
                    300, movie_duration - 300
                )  # минимум 5 минут
                pause_position = total_watched
                ended_at = None

            device_type = random.choices(device_types, weights=device_weights, k=1)[0]
            quality = random.choices(qualities, weights=quality_weights, k=1)[0]

            yield ViewingSession(
                session_id=session_id,
                user_id=user_id,
                movie_id=movie_id,
                started_at=started_at,
                ended_at=ended_at,
                pause_position_seconds=pause_position,
                total_watched_seconds=total_watched,
                device_type=device_type,
                quality=quality,
                is_completed=is_completed,
            )

    def generate_user_activities(
        self, count: int, user_count: int
    ) -> Iterator[UserActivity]:
        """
        Генерирует активности пользователей

        Args:
            count: Количество активностей
            user_count: Общее количество пользователей (используем сгенерированные UUIDs)

        Yields:
            UserActivity: Объект активности пользователя
        """
        if not self._generated_user_ids:
            raise ValueError("Необходимо сначала сгенерировать пользователей перед генерацией активностей")

        activity_types = [
            "login",
            "logout",
            "search",
            "play",
            "pause",
            "rate",
            "browse",
        ]
        activity_weights = [0.15, 0.15, 0.20, 0.20, 0.10, 0.05, 0.15]

        search_queries = [
            "комедия",
            "ужасы",
            "драма",
            "боевик",
            "мелодрама",
            "фантастика",
            "новинки",
            "топ фильмы",
            "русские фильмы",
            "зарубежные фильмы",
        ]

        for _ in range(count):
            self._activity_id_counter += 1
            activity_id = self._activity_id_counter

            user_id = self._get_random_user_id()
            activity_type = random.choices(
                activity_types, weights=activity_weights, k=1
            )[0]

            # Генерация дополнительных данных в зависимости от типа активности
            activity_data = None
            if activity_type == "search":
                activity_data = {"query": random.choice(search_queries)}
            elif activity_type in ["play", "pause"]:
                activity_data = {
                    "movie_id": random.randint(1, 10000),
                    "position": random.randint(0, 7200),
                }
            elif activity_type == "rate":
                activity_data = {
                    "movie_id": random.randint(1, 10000),
                    "rating": random.randint(1, 10),
                }

            timestamp = self.fake.date_time_between(
                start_date=datetime(2021, 1, 1),  # С 2021 года
                end_date=datetime(2023, 12, 31),  # До конца 2023
            )

            # IP адрес для части активностей
            ip_address = self.fake.ipv4() if random.random() < 0.8 else None

            # User Agent для части активностей
            user_agent = self.fake.user_agent() if random.random() < 0.6 else None

            yield UserActivity(
                activity_id=activity_id,
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data,
                timestamp=timestamp,
                ip_address=ip_address,
                user_agent=user_agent,
            )

    def generate_batch(self, generator: Iterator, batch_size: int) -> list:
        """
        Генерирует данные батчами для эффективной вставки

        Args:
            generator: Генератор данных
            batch_size: Размер батча

        Returns:
            list: Батч данных
        """
        return list(islice(generator, batch_size))

    def estimate_data_size(self, config: BenchmarkConfig) -> dict:
        """
        Оценивает размер данных для конфигурации

        Args:
            config: Конфигурация бенчмарка

        Returns:
            dict: Оценка размеров данных
        """
        # Примерные размеры записей в байтах (UUID увеличивает размер user записей)
        sizes = {
            "user": 250,
            "movie": 500,
            "rating": 170,
            "viewing_session": 270,
            "user_activity": 320,
        }

        total_records = (
            config.num_users
            + config.num_movies
            + config.num_ratings
            + config.num_sessions
            + config.num_activities
        )

        total_size_mb = (
            (
                config.num_users * sizes["user"]
                + config.num_movies * sizes["movie"]
                + config.num_ratings * sizes["rating"]
                + config.num_sessions * sizes["viewing_session"]
                + config.num_activities * sizes["user_activity"]
            )
            / 1024
            / 1024
        )

        return {
            "total_records": total_records,
            "estimated_size_mb": round(total_size_mb, 2),
            "estimated_generation_time_minutes": round(
                total_records / 50000, 1
            ),  # ~50k записей в минуту
        }