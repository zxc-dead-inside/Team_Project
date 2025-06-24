import logging
import random
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm

from db_clients.base_client import DBClient
from logger import  setup_logging

setup_logging()


class PostgresClient(DBClient):
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.db_config["db_name"],
                user=self.db_config["db_user"],
                password=self.db_config["password"],
                host=self.db_config["host"],
                port=self.db_config["port"]
                # **self.db_config
            )
            self.conn.autocommit = True
            self.cur = self.conn.cursor()
            logging.info("Connected to PostgreSQL")
        except Exception as e:
            logging.error(f"PostgreSQL connection error: {e}")
            raise
    
    def disconnect(self):
        if hasattr(self, 'cur') and self.cur:
            self.cur.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        logging.info("Disconnected from PostgreSQL")
    
    def initialize_schema(self):
        try:
            self.cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id UUID PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS movies (
                movie_id UUID PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                year INTEGER,
                genre VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS reviews (
                review_id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(user_id),
                movie_id UUID REFERENCES movies(movie_id),
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS review_ratings (
                rating_id UUID PRIMARY KEY,
                review_id UUID REFERENCES reviews(review_id),
                user_id UUID REFERENCES users(user_id),
                rating SMALLINT NOT NULL CHECK (rating IN (-1, 1)),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS bookmarks (
                bookmark_id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(user_id),
                movie_id UUID REFERENCES movies(movie_id),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS favorites (
                favorite_id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(user_id),
                movie_id UUID REFERENCES movies(movie_id),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS view_history (
                history_id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(user_id),
                movie_id UUID REFERENCES movies(movie_id),
                viewed_at TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            );
            """)
            logging.info("PostgreSQL schema initialized")
        except Exception as e:
            logging.error(f"Schema initialization error: {e}")
            raise
    
    def cleanup(self):
        """Полная очистка всех данных в PostgreSQL"""
        try:
            logging.info("Cleaning up PostgreSQL database...")
            
            # Отключаем триггеры и ограничения для безопасного удаления
            self.cur.execute("SET session_replication_role = 'replica';")
            
            # Удаляем все таблицы в правильном порядке (с учетом зависимостей)
            tables = [
                "review_ratings", "reviews", 
                "bookmarks", "favorites", "view_history",
                "users", "movies"
            ]
            
            for table in tables:
                try:
                    self.cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                    logging.info(f"Dropped table: {table}")
                except Exception as e:
                    logging.error(f"Error dropping table {table}: {e}")
            
            # Восстанавливаем настройки
            self.cur.execute("SET session_replication_role = 'origin';")
            self.conn.commit()
            
            logging.info("PostgreSQL cleanup completed")
        except Exception as e:
            logging.error(f"PostgreSQL cleanup failed: {e}")
            self.conn.rollback()

    def load_ids_cache(self):
        """Загрузка ID в кеш для использования в тестах"""
        if not self.conn:
            self.connect()
            
        with self.conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users")
            self.user_ids = [row[0] for row in cur.fetchall()]
            
            cur.execute("SELECT movie_id FROM movies")
            self.movie_ids = [row[0] for row in cur.fetchall()]
            
            cur.execute("SELECT review_id FROM reviews")
            self.review_ids = [row[0] for row in cur.fetchall()]
        
        logging.info(f"Loaded {len(self.user_ids)} users, {len(self.movie_ids)} movies, {len(self.review_ids)} reviews to cache")
    
    def generate_test_data(self, total_records: int):
        try:
            start_time = datetime.now()
            record_counts = self._calculate_record_counts(total_records)
            
            logging.info(f"Generating test data for PostgreSQL: {record_counts}")
            self._generate_users(record_counts['users'])
            self._generate_movies(record_counts['movies'])
            self._generate_reviews(record_counts['reviews'])
            self._generate_ratings(record_counts['review_ratings'])
            self._generate_bookmarks(record_counts['bookmarks'])
            self._generate_favorites(record_counts['favorites'])
            self._generate_history(record_counts['history'])
            self._create_indexes()
            
            duration = (datetime.now() - start_time).total_seconds()
            logging.info(f"Data generation completed in {duration:.2f} seconds")
            self.data_generated = True
            
        except Exception as e:
            logging.error(f"Data generation failed: {e}")
            raise
    
    def _generate_users(self, count: int):
        """Генерация пользователей"""

        batch_size = 10000
        for i in tqdm(range(0, count, batch_size), desc="Generating usesrs"):
            batch = []
            current_batch = min(batch_size, count - i)
            for _ in range(current_batch):
                user_id = self._generate_uuid()
                self.user_ids.append(user_id)
                batch.append((
                    user_id,
                    self.fake.user_name(),
                    self.fake.email(),
                    self.fake.date_time_between(start_date="-5y")
                ))
            
            execute_values(
                self.cur,
                "INSERT INTO users (user_id, username, email, created_at) VALUES %s",
                batch
            )
        logging.info(f"Generated {count} users")
    
    def _generate_movies(self, count: int):
        """Генерация фильмов"""
        batch_size = 10000
        genres = ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance"]
        for i in tqdm(range(0, count, batch_size), desc="Generating movies"):
            batch = []
            current_batch = min(batch_size, count - i)
            for _ in range(current_batch):
                movie_id = self._generate_uuid()
                self.movie_ids.append(movie_id)
                batch.append((
                    movie_id,
                    self.fake.sentence(nb_words=3),
                    random.randint(1950, 2023),
                    random.choice(genres),
                    self.fake.date_time_between(start_date="-10y")
                ))
            
            execute_values(
                self.cur,
                "INSERT INTO movies (movie_id, title, year, genre, created_at) VALUES %s",
                batch
            )
        logging.info(f"Generated {count} movies")
    
    def _generate_reviews(self, count: int):
        """Генерация рецензий"""
        batch_size = 10000
        for i in tqdm(range(0, count, batch_size), desc="Generating reviews"):
            batch = []
            current_batch = min(batch_size, count - i)
            for _ in range(current_batch):
                review_id = self._generate_uuid()
                self.review_ids.append(review_id)
                batch.append((
                    review_id,
                    random.choice(self.user_ids),
                    random.choice(self.movie_ids),
                    self.fake.paragraph(nb_sentences=5),
                    self.fake.date_time_between(start_date="-2y")
                ))
            
            execute_values(
                self.cur,
                "INSERT INTO reviews (review_id, user_id, movie_id, text, created_at) VALUES %s",
                batch
            )
        logging.info(f"Generated {count} reviews")
    
    def _generate_ratings(self, count: int):
        """Генерация оценок"""
        batch_size = 10000
        for i in tqdm(range(0, count, batch_size), desc="Generating  ratings"):
            batch = []
            current_batch = min(batch_size, count - i)
            for _ in range(current_batch):
                batch.append((
                    self._generate_uuid(),
                    random.choice(self.review_ids),
                    random.choice(self.user_ids),
                    random.choice([-1, 1]),
                    self.fake.date_time_between(start_date="-1y")
                ))
            
            execute_values(
                self.cur,
                "INSERT INTO review_ratings (rating_id, review_id, user_id, rating, created_at) VALUES %s",
                batch
            )
        logging.info(f"Generated {count} ratings")
    
    def _generate_bookmarks(self, count: int):
        """Генерация закладок"""
        self._generate_relations(
            count, 
            "bookmarks", 
            "bookmark_id",
            self.fake.date_time_between(start_date="-1y"),
            "Generating bookomarks"
        )
        logging.info(f"Generated {count} bookmarks")
    
    def _generate_favorites(self, count: int):
        """Генерация избранного"""
        self._generate_relations(
            count, 
            "favorites", 
            "favorite_id",
            self.fake.date_time_between(start_date="-1y"),
            "Generating favorites"
        )
        logging.info(f"Generated {count} favorites")
    
    def _generate_history(self, count: int):
        """Генерация истории просмотров"""
        self._generate_relations(
            count, 
            "view_history", 
            "history_id",
            self.fake.date_time_between(start_date="-30d"),
            "Generating history"
        )
        logging.info(f"Generated {count} history records")
    
    def _generate_relations(
            self, count: int, table: str, id_field: str, timestamp, task: str):
        """Общая функция для генерации связей"""
        batch_size = 10000
        for i in tqdm(range(0, count, batch_size), desc=task):
            batch = []
            current_batch = min(batch_size, count - i)
            for _ in range(current_batch):
                batch.append((
                    self._generate_uuid(),
                    random.choice(self.user_ids),
                    random.choice(self.movie_ids),
                    timestamp
                ))
            
            execute_values(
                self.cur,
                f"INSERT INTO {table} ({id_field}, user_id, movie_id, created_at) VALUES %s",
                batch
            )
    
    def _create_indexes(self):
        """Создание индексов для ускорения запросов"""
        self.cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_movie ON reviews(movie_id);
        CREATE INDEX IF NOT EXISTS idx_ratings_review ON review_ratings(review_id);
        CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id);
        CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
        CREATE INDEX IF NOT EXISTS idx_history_user ON view_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at);
        CREATE INDEX IF NOT EXISTS idx_reviews_created ON reviews(created_at);
        """)
        logging.info("Indexes created")
    
    # Тестовые методы
    def test_insert_review(self) -> int:
        try:
            review_id = self._generate_uuid()
            self.cur.execute(
                "INSERT INTO reviews (review_id, user_id, movie_id, text, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (review_id, random.choice(self.user_ids), random.choice(self.movie_ids), 
                 self.fake.paragraph(), datetime.now())
            )
            return 1
        except Exception as e:
            logging.error(f"test_insert_review failed: {e}")
            return 0
    
    def test_get_reviews(self) -> int:
        try:
            self.cur.execute(
                "SELECT review_id, text FROM reviews "
                "WHERE movie_id = %s "
                "ORDER BY created_at DESC "
                "LIMIT 10",
                (random.choice(self.movie_ids),))
            return len(self.cur.fetchall())
        except Exception as e:
            logging.error(f"test_get_reviews failed: {e}")
            return 0
    
    def test_add_rating(self) -> int:
        try:
            self.cur.execute(
                "INSERT INTO review_ratings (rating_id, review_id, user_id, rating, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (self._generate_uuid(), random.choice(self.review_ids), 
                 random.choice(self.user_ids), random.choice([-1, 1]), datetime.now())
            )
            return 1
        except Exception as e:
            logging.error(f"test_add_rating failed: {e}")
            return 0
    
    def test_get_ratings_summary(self) -> int:
        try:
            self.cur.execute(
                "SELECT "
                "  COUNT(CASE WHEN rating = 1 THEN 1 END) AS likes, "
                "  COUNT(CASE WHEN rating = -1 THEN 1 END) AS dislikes "
                "FROM review_ratings "
                "WHERE review_id = %s",
                (random.choice(self.review_ids),))
            result = self.cur.fetchone()
            return 1 if result else 0
        except Exception as e:
            logging.error(f"test_get_ratings_summary failed: {e}")
            return 0
    
    def test_add_bookmark(self) -> int:
        try:
            self.cur.execute(
                "INSERT INTO bookmarks (bookmark_id, user_id, movie_id, created_at) "
                "VALUES (%s, %s, %s, %s)",
                (self._generate_uuid(), random.choice(self.user_ids), 
                 random.choice(self.movie_ids), datetime.now())
            )
            return 1
        except Exception as e:
            logging.error(f"test_add_bookmark failed: {e}")
            return 0
    
    def test_get_user_bookmarks(self) -> int:
        try:
            self.cur.execute(
                "SELECT movie_id FROM bookmarks "
                "WHERE user_id = %s "
                "ORDER BY created_at DESC "
                "LIMIT 10",
                (random.choice(self.user_ids),))
            return len(self.cur.fetchall())
        except Exception as e:
            logging.error(f"test_get_user_bookmarks failed: {e}")
            return 0
    
    def test_complex_query(self) -> int:
        try:
            self.cur.execute("""
            SELECT 
                m.title,
                m.year,
                (SELECT COUNT(*) FROM reviews r WHERE r.movie_id = m.movie_id) AS review_count,
                (SELECT COUNT(*) FROM bookmarks b WHERE b.movie_id = m.movie_id) AS bookmark_count
            FROM view_history vh
            JOIN movies m ON vh.movie_id = m.movie_id
            WHERE vh.user_id = %s
            GROUP BY m.movie_id
            ORDER BY MAX(vh.viewed_at) DESC
            LIMIT 5
            """, (random.choice(self.user_ids),))
            return len(self.cur.fetchall())
        except Exception as e:
            logging.error(f"test_complex_query failed: {e}")
            return 0
    
    # Аналитические запросы
    def test_top_movies_by_comments(self) -> int:
        """Топ-10 фильмов с наибольшим количеством комментариев"""
        try:
            self.cur.execute("""
            SELECT m.movie_id, m.title, COUNT(r.review_id) AS comment_count
            FROM movies m
            JOIN reviews r ON m.movie_id = r.movie_id
            GROUP BY m.movie_id
            ORDER BY comment_count DESC
            LIMIT 10
            """)
            return len(self.cur.fetchall())
        except Exception as e:
            logging.error(f"test_top_movies_by_comments failed: {e}")
            return 0
    
    def test_top_helpful_reviews(self) -> int:
        """Топ-5 самых полезных комментариев к фильму (лайки > дизлайки)"""
        try:
            movie_id = random.choice(self.movie_ids)
            self.cur.execute("""
            WITH review_stats AS (
                SELECT 
                    r.review_id,
                    COUNT(CASE WHEN rr.rating = 1 THEN 1 END) AS likes,
                    COUNT(CASE WHEN rr.rating = -1 THEN 1 END) AS dislikes
                FROM reviews r
                LEFT JOIN review_ratings rr ON r.review_id = rr.review_id
                WHERE r.movie_id = %s
                GROUP BY r.review_id
            )
            SELECT r.review_id, r.text, s.likes, s.dislikes
            FROM review_stats s
            JOIN reviews r ON s.review_id = r.review_id
            WHERE s.likes > s.dislikes
            ORDER BY (s.likes - s.dislikes) DESC
            LIMIT 5
            """, (movie_id,))
            return len(self.cur.fetchall())
        except Exception as e:
            logging.error(f"test_top_helpful_reviews failed: {e}")
            return 0
    
    def test_top_users_by_comments(self) -> int:
        """Топ-10 пользователей с наибольшим количеством оставленных комментариев"""
        try:
            self.cur.execute("""
            SELECT u.user_id, u.username, COUNT(r.review_id) AS comment_count
            FROM users u
            JOIN reviews r ON u.user_id = r.user_id
            GROUP BY u.user_id
            ORDER BY comment_count DESC
            LIMIT 10
            """)
            return len(self.cur.fetchall())
        except Exception as e:
            logging.error(f"test_top_users_by_comments failed: {e}")
            return 0