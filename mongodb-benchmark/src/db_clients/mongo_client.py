import logging
import random
from datetime import datetime

from pymongo import MongoClient
from tqdm import tqdm

from db_clients.base_client import DBClient
from logger import setup_logging


setup_logging()


class MongoClientWrapper(DBClient):
    def connect(self):
        """Подключение к БД."""

        try:
            self.client = MongoClient(
                host=self.db_config['host'],
                port=self.db_config['port'],
                username=self.db_config['db_username'],
                password=self.db_config['password'],
                authSource=self.db_config['authSource']
            )
            self.db = self.client[self.db_config['db_name']]
            logging.info("Connected to MongoDB")
        except Exception as e:
            logging.error(f"MongoDB connection error: {e}")
            raise
    
    def disconnect(self):
        """Отключение о БД."""

        if hasattr(self, 'client') and self.client:
            self.client.close()
        logging.info("Disconnected from MongoDB")
    
    def initialize_schema(self):
        """Заглушка для MongoDB"""
        # MongoDB не требует явного создания схемы
        logging.info("MongoDB schema initialization skipped (schema-less)")

    def load_ids_cache(self):
        """Загрузка ID в кеш для использования в тестах"""

        try:
            self.user_ids = [doc['user_id'] for doc in self.db.users.find({}, {'user_id': 1})]
            self.movie_ids = [doc['movie_id'] for doc in self.db.movies.find({}, {'movie_id': 1})]
            self.review_ids = [doc['review_id'] for doc in self.db.reviews.find({}, {'review_id': 1})]
            
            logging.info(f"Loaded {len(self.user_ids)} users, {len(self.movie_ids)} movies, {len(self.review_ids)} reviews to cache")
        except Exception as e:
            logging.error(f"Failed to load IDs: {e}")
            # Инициализируем пустые списки, чтобы избежать ошибок в тестах
            self.user_ids = []
            self.movie_ids = []
            self.review_ids = []
    
    def cleanup(self):
        """Полная очистка всех данных в MongoDB"""

        try:
            logging.info("Cleaning up MongoDB database...")
            
            # Получаем список всех коллекций
            collections = self.db.list_collection_names()
            
            # Удаляем каждую коллекцию
            for collection in collections:
                try:
                    self.db[collection].drop()
                    logging.info(f"Dropped collection: {collection}")
                except Exception as e:
                    logging.error(f"Error dropping collection {collection}: {e}")
            
            logging.info("MongoDB cleanup completed")
        except Exception as e:
            logging.error(f"MongoDB cleanup failed: {e}")


    def generate_test_data(self, total_records: int):
        """Общий метод запускающией генерацию данных"""

        try:
            start_time = datetime.now()
            record_counts = self._calculate_record_counts(total_records)
            
            logging.info(f"Generating test data for MongoDB: {record_counts}")
            
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
        """Генерация пользователей."""

        batch_size = 10000
        users = []
        for _ in tqdm(range(count),desc="Generating users"):
            user_id = self._generate_uuid()
            self.user_ids.append(user_id)
            users.append({
                "user_id": user_id,
                "username": self.fake.user_name(),
                "email": self.fake.email(),
                "created_at": self.fake.date_time_between(start_date="-5y")
            })
            
            if len(users) >= batch_size:
                self.db.users.insert_many(users)
                users = []
        
        if users:
            self.db.users.insert_many(users)
        logging.info(f"Generated {count} users")
    
    def _generate_movies(self, count: int):
        """Генерация ревью."""

        batch_size = 10000
        movies = []
        genres = ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance"]
        for _ in tqdm(range(count), desc="Generating movies"):
            movie_id = self._generate_uuid()
            self.movie_ids.append(movie_id)
            movies.append({
                "movie_id": movie_id,
                "title": self.fake.sentence(nb_words=3),
                "year": random.randint(1950, 2023),
                "genre": random.choice(genres),
                "created_at": self.fake.date_time_between(start_date="-10y")
            })
            
            if len(movies) >= batch_size:
                self.db.movies.insert_many(movies)
                movies = []
        
        if movies:
            self.db.movies.insert_many(movies)
        logging.info(f"Generated {count} movies")
    
    def _generate_reviews(self, count: int):
        """Генерация ревью."""

        batch_size = 10000
        reviews = []
        for _ in tqdm(range(count), desc="Generating reviews"):
            review_id = self._generate_uuid()
            self.review_ids.append(review_id)
            reviews.append({
                "review_id": review_id,
                "user_id": random.choice(self.user_ids),
                "movie_id": random.choice(self.movie_ids),
                "text": self.fake.paragraph(nb_sentences=5),
                "created_at": self.fake.date_time_between(start_date="-2y")
            })
            
            if len(reviews) >= batch_size:
                self.db.reviews.insert_many(reviews)
                reviews = []
        
        if reviews:
            self.db.reviews.insert_many(reviews)
        logging.info(f"Generated {count} reviews")
    
    def _generate_ratings(self, count: int):
        """Генерация рейтнга."""

        batch_size = 10000
        ratings = []
        for _ in tqdm(range(count), desc="Generating ratings"):
            ratings.append({
                "rating_id": self._generate_uuid(),
                "review_id": random.choice(self.review_ids),
                "user_id": random.choice(self.user_ids),
                "rating": random.choice([-1, 1]),
                "created_at": self.fake.date_time_between(start_date="-1y")
            })
            
            if len(ratings) >= batch_size:
                self.db.review_ratings.insert_many(ratings)
                ratings = []
        
        if ratings:
            self.db.review_ratings.insert_many(ratings)
        logging.info(f"Generated {count} ratings")
    
    def _generate_bookmarks(self, count: int):
        """Генерация закладок"""
        self._generate_relations(
            count, 
            "bookmarks", 
            "bookmark_id",
            self.fake.date_time_between(start_date="-1y"),
            "Generating bookmarks"
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
        """Генерация истории"""
    
        self._generate_relations(
            count, 
            "view_history", 
            "history_id",
            self.fake.date_time_between(start_date="-30d"),
            "Generating history"
        )
        logging.info(f"Generated {count} history records")
    
    def _generate_relations(
            self, count: int, collection: str, id_field: str, timestamp, task: str):
        """Общая функция для генерации связей"""
        batch_size = 10000
        records = []
        for _ in tqdm(range(count), desc=task):
            records.append({
                id_field: self._generate_uuid(),
                "user_id": random.choice(self.user_ids),
                "movie_id": random.choice(self.movie_ids),
                "created_at": timestamp
            })
            
            if len(records) >= batch_size:
                getattr(self.db, collection).insert_many(records)
                records = []
        
        if records:
            getattr(self.db, collection).insert_many(records)
    
    def _create_indexes(self):
        """Создание индексов для ускорения запросов"""
        self.db.reviews.create_index("movie_id")
        self.db.review_ratings.create_index("review_id")
        self.db.bookmarks.create_index("user_id")
        self.db.favorites.create_index("user_id")
        self.db.view_history.create_index("user_id")
        self.db.users.create_index("created_at")
        self.db.reviews.create_index("created_at")
        logging.info("Indexes created")
    
    def test_insert_review(self) -> int:
        try:
            self.db.reviews.insert_one({
                "review_id": self._generate_uuid(),
                "user_id": random.choice(self.user_ids),
                "movie_id": random.choice(self.movie_ids),
                "text": self.fake.paragraph(),
                "created_at": datetime.now()
            })
            return 1
        except Exception as e:
            logging.error(f"test_insert_review failed: {e}")
            return 0
    
    def test_get_reviews(self) -> int:
        try:
            reviews = list(self.db.reviews.find(
                {"movie_id": random.choice(self.movie_ids)},
                {"review_id": 1, "text": 1}
            ).sort("created_at", -1).limit(10))
            return len(reviews)
        except Exception as e:
            logging.error(f"test_get_reviews failed: {e}")
            return 0
    
    def test_add_rating(self) -> int:
        try:
            self.db.review_ratings.insert_one({
                "rating_id": self._generate_uuid(),
                "review_id": random.choice(self.review_ids),
                "user_id": random.choice(self.user_ids),
                "rating": random.choice([-1, 1]),
                "created_at": datetime.now()
            })
            return 1
        except Exception as e:
            logging.error(f"test_add_rating failed: {e}")
            return 0
    
    def test_get_ratings_summary(self) -> int:
        try:
            review_id = random.choice(self.review_ids)
            ratings = list(self.db.review_ratings.find({"review_id": review_id}))
            
            likes = sum(1 for r in ratings if r['rating'] == 1)
            dislikes = sum(1 for r in ratings if r['rating'] == -1)
            
            return 1 if ratings else 0
        except Exception as e:
            logging.error(f"test_get_ratings_summary failed: {e}")
            return 0
    
    def test_add_bookmark(self) -> int:
        try:
            self.db.bookmarks.insert_one({
                "bookmark_id": self._generate_uuid(),
                "user_id": random.choice(self.user_ids),
                "movie_id": random.choice(self.movie_ids),
                "created_at": datetime.now()
            })
            return 1
        except Exception as e:
            logging.error(f"test_add_bookmark failed: {e}")
            return 0
    
    def test_get_user_bookmarks(self) -> int:
        try:
            bookmarks = list(self.db.bookmarks.find(
                {"user_id": random.choice(self.user_ids)},
                {"movie_id": 1}
            ).sort("created_at", -1).limit(10))
            return len(bookmarks)
        except Exception as e:
            logging.error(f"test_get_user_bookmarks failed: {e}")
            return 0
    
    def test_complex_query(self) -> int:
        try:
            pipeline = [
                {"$match": {"user_id": random.choice(self.user_ids)}},
                {"$lookup": {
                    "from": "movies",
                    "localField": "movie_id",
                    "foreignField": "movie_id",
                    "as": "movie"
                }},
                {"$unwind": "$movie"},
                {"$group": {
                    "_id": "$movie_id",
                    "title": {"$first": "$movie.title"},
                    "year": {"$first": "$movie.year"},
                    "last_viewed": {"$max": "$viewed_at"},
                    "review_count": {
                        "$sum": {
                            "$size": {
                                "$ifNull": [
                                    {"$filter": {
                                        "input": {"$objectToArray": "$movie.reviews"},
                                        "cond": {"$eq": ["$$this.k", "count"]}
                                    }},
                                    []
                                ]
                            }
                        }
                    },
                    "bookmark_count": {
                        "$sum": {
                            "$size": {
                                "$ifNull": [
                                    {"$filter": {
                                        "input": {"$objectToArray": "$movie.bookmarks"},
                                        "cond": {"$eq": ["$$this.k", "count"]}
                                    }},
                                    []
                                ]
                            }
                        }
                    }
                }},
                {"$sort": {"last_viewed": -1}},
                {"$limit": 5}
            ]
            
            result = list(self.db.view_history.aggregate(pipeline))
            return len(result)
        except Exception as e:
            logging.error(f"test_complex_query failed: {e}")
            return 0
    
    def test_top_movies_by_comments(self) -> int:
        try:
            pipeline = [
                {"$group": {
                    "_id": "$movie_id",
                    "comment_count": {"$sum": 1}
                }},
                {"$sort": {"comment_count": -1}},
                {"$limit": 10},
                {"$lookup": {
                    "from": "movies",
                    "localField": "_id",
                    "foreignField": "movie_id",
                    "as": "movie"
                }},
                {"$unwind": "$movie"},
                {"$project": {
                    "movie_id": "$_id",
                    "title": "$movie.title",
                    "comment_count": 1
                }}
            ]
            
            result = list(self.db.reviews.aggregate(pipeline))
            return len(result)
        except Exception as e:
            logging.error(f"test_top_movies_by_comments failed: {e}")
            return 0
    
    def test_top_helpful_reviews(self) -> int:
        try:
            movie_id = random.choice(self.movie_ids)
            pipeline = [
                {"$match": {"movie_id": movie_id}},
                {"$lookup": {
                    "from": "review_ratings",
                    "localField": "review_id",
                    "foreignField": "review_id",
                    "as": "ratings"
                }},
                {"$unwind": "$ratings"},
                {"$group": {
                    "_id": "$review_id",
                    "text": {"$first": "$text"},
                    "likes": {"$sum": {"$cond": [{"$eq": ["$ratings.rating", 1]}, 1, 0]}},
                    "dislikes": {"$sum": {"$cond": [{"$eq": ["$ratings.rating", -1]}, 1, 0]}}
                }},
                {"$match": {
                    "$expr": {"$gt": ["$likes", "$dislikes"]}
                }},
                {"$project": {
                    "review_id": "$_id",
                    "text": 1,
                    "helpfulness": {"$subtract": ["$likes", "$dislikes"]}
                }},
                {"$sort": {"helpfulness": -1}},
                {"$limit": 5}
            ]
            
            result = list(self.db.reviews.aggregate(pipeline))
            return len(result)
        except Exception as e:
            logging.error(f"test_top_helpful_reviews failed: {e}")
            return 0
    
    def test_top_users_by_comments(self) -> int:
        try:
            pipeline = [
                {"$group": {
                    "_id": "$user_id",
                    "comment_count": {"$sum": 1}
                }},
                {"$sort": {"comment_count": -1}},
                {"$limit": 10},
                {"$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "user_id",
                    "as": "user"
                }},
                {"$unwind": "$user"},
                {"$project": {
                    "user_id": "$_id",
                    "username": "$user.username",
                    "comment_count": 1
                }}
            ]
            
            result = list(self.db.reviews.aggregate(pipeline))
            return len(result)
        except Exception as e:
            logging.error(f"test_top_users_by_comments failed: {e}")
            return 0