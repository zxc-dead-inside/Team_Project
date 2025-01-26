from elasticsearch import Elasticsearch, helpers
import backoff
from typing import List, Dict, Any
from logger_setup import logger


class ElasticsearchLoader:
    def __init__(self, host: str, port: int):
        self.es = Elasticsearch([{"host": host, "port": port, "scheme": "http"}])

        self.index_config = {
            "settings": {
                "refresh_interval": "1s",
                "analysis": {
                    "filter": {
                        "english_stop": {"type": "stop", "stopwords": "_english_"},
                        "english_stemmer": {"type": "stemmer", "language": "english"},
                        "english_possessive_stemmer": {
                            "type": "stemmer",
                            "language": "possessive_english",
                        },
                        "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                        "russian_stemmer": {"type": "stemmer", "language": "russian"},
                    },
                    "analyzer": {
                        "ru_en": {
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "english_stop",
                                "english_stemmer",
                                "english_possessive_stemmer",
                                "russian_stop",
                                "russian_stemmer",
                            ],
                        }
                    },
                },
            },
            "mappings": {
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "imdb_rating": {"type": "float"},
                    "title": {
                        "type": "text",
                        "analyzer": "ru_en",
                        "fields": {"raw": {"type": "keyword"}},
                    },
                    "description": {"type": "text", "analyzer": "ru_en"},
                    "actors_names": {"type": "text", "analyzer": "ru_en"},
                    "writers_names": {"type": "text", "analyzer": "ru_en"},
                    "directors_names": {"type": "text", "analyzer": "ru_en"},
                    "genres": {"type": "keyword"},
                    "actors": {
                        "type": "nested",
                        "dynamic": "strict",
                        "properties": {
                            "id": {"type": "keyword"},
                            "name": {"type": "text", "analyzer": "ru_en"},
                        },
                    },
                    "directors": {
                        "type": "nested",
                        "dynamic": "strict",
                        "properties": {
                            "id": {"type": "keyword"},
                            "name": {"type": "text", "analyzer": "ru_en"},
                        },
                    },
                    "writers": {
                        "type": "nested",
                        "dynamic": "strict",
                        "properties": {
                            "id": {"type": "keyword"},
                            "name": {"type": "text", "analyzer": "ru_en"},
                        },
                    },
                },
            },
        }

        @backoff.on_exception(backoff.expo, Exception, max_tries=10)
        def wait_for_es():
            if not self.es.ping():
                raise ConnectionError("Elasticsearch is not ready")

            # Create index with mapping if it doesn't exist
            if not self.es.indices.exists(index="movies"):
                self.es.indices.create(index="movies", body=self.index_config)

        wait_for_es()

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    def load_movies(self, movies: List[Dict[str, Any]]):
        sanitized_movies = []
        for movie in movies:
            try:
                # Create a new dict with only the fields we want to index
                sanitized_movie = {
                    "id": movie["id"],
                    "imdb_rating": movie.get("imdb_rating", None),
                    "title": movie.get("title", ""),
                    "description": movie.get("description", ""),
                    "actors_names": movie.get("actors_names", []),
                    "writers_names": movie.get("writers_names", []),
                    "directors_names": movie.get("directors_names", []),
                    "genres": movie.get("genres", []),
                    "actors": movie.get("actors", []),
                    "directors": movie.get("directors", []),
                    "writers": movie.get("writers", []),
                }

                # Replace None values with appropriate defaults
                for key, value in sanitized_movie.items():
                    if value is None:
                        if key == "imdb_rating":
                            sanitized_movie[key] = 0.0  # Default value for imdb_rating
                        else:
                            sanitized_movie[key] = (
                                []
                                if key.endswith("_names")
                                or key in ["genres", "actors", "directors", "writers"]
                                else ""
                            )

                sanitized_movies.append(sanitized_movie)
            except Exception as e:
                logger.error(f"Error sanitizing movie: {movie}, error: {e}")

        actions = [
            {"_index": "movies", "_id": movie["id"], "_source": movie}
            for movie in sanitized_movies
        ]

        try:
            helpers.bulk(self.es, actions)
        except helpers.BulkIndexError as e:
            logger.error(f"Bulk index error: {e}")
            for error in e.errors:
                logger.error(f"Failed document: {error}")
            raise
