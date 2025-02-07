from typing import Any

import backoff
from elasticsearch import Elasticsearch, helpers

from config import es_indices_settings as esis
from logger_setup import logger
from state import State


class ElasticsearchLoader:
    def __init__(self, host: str, port: int):
        self.es = Elasticsearch(
            [{"host": host, "port": port, "scheme": "http"}]
        )

        self.index_movies = {
            "settings": {
                "refresh_interval": "1s",
                "analysis": {
                    "filter": {
                        "english_stop": {
                            "type": "stop",
                            "stopwords": "_english_"
                        },
                        "english_stemmer": {
                            "type": "stemmer",
                            "language": "english"
                        },
                        "english_possessive_stemmer": {
                            "type": "stemmer",
                            "language": "possessive_english",
                        },
                        "russian_stop": {
                            "type": "stop",
                            "stopwords": "_russian_"
                            },
                        "russian_stemmer": {
                            "type": "stemmer",
                            "language": "russian"
                        },
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
                    "genres": {
                        "type": "nested",
                        "dynamic": "strict",
                        "properties": {
                            "id": {
                                "type": "keyword"
                            },
                            "name": {
                                "type": "text",
                                "analyzer": "ru_en"
                            }
                        }
                    },
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

        self.index_persons = {
            "settings": {
                "refresh_interval": "1s",
                "analysis": {
                    "filter": {
                        "english_stop": {
                            "type": "stop",
                            "stopwords": "_english_"
                        },
                        "english_stemmer": {
                            "type": "stemmer",
                            "language": "english"
                        },
                        "english_possessive_stemmer": {
                            "type": "stemmer",
                            "language": "possessive_english"
                        },
                        "russian_stop": {
                            "type": "stop",
                            "stopwords": "_russian_"
                        },
                        "russian_stemmer": {
                            "type": "stemmer",
                            "language": "russian"
                        }
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
                                "russian_stemmer"
                            ]
                        }
                    }
                }
            },
            "mappings": {
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "full_name": {
                        "type": "text",
                        "analyzer": "ru_en",
                        "fields": {
                            "raw": {
                                "type": "keyword"
                            }
                        }
                    },
                    "films": {
                        "type": "nested",
                        "dynamic": "strict",
                        "properties": {
                            "id": {"type": "keyword"},
                            "roles": {"type": "text", "analyzer": "ru_en"}
                        }
                    }
                }
            }
        }

        @backoff.on_exception(backoff.expo, Exception, max_tries=10)
        def wait_for_es():
            if not self.es.ping():
                raise ConnectionError("Elasticsearch is not ready")

            # Create index with mapping if it doesn't exist
            if not self.es.indices.exists(index="movies"):
                self.es.indices.create(index="movies", body=self.index_movies)
            if not self.es.indices.exists(index='genres'):
                self.es.indices.create(
                    index='genres', mappings=esis.genres_mappings
                )
            if not self.es.indices.exists(index="persons"):
                self.es.indices.create(
                    index="persons",
                    body=self.index_persons
                )

        wait_for_es()

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    def load_genres(self, genres: list[dict[str, Any]]):
        state = State()
        sanitized_genres = []
        for genre in genres:
            try:
                sanitized_genre = {
                    "id": genre["id"],
                    "name": genre.get("name", "")
                }
                sanitized_genres.append(sanitized_genre)
            except Exception as e:
                logger.error(
                    f"Error sanitizing movie: {genre}, error: {e}")
        actions = [
                {"_index": "genres",
                 "_id": genre["id"],
                 "_source": genre}
                for genre in sanitized_genres
            ]
        try:
            helpers.bulk(self.es, actions)
            state.increment_processed('genres', len(genres))
            stats = state.get_statistics('genres')
            logger.info(
                f"Successfully processed {len(genres)} genres. "
                f"Total processed: {stats['total_processed']}")
        except helpers.BulkIndexError as e:
            logger.error(f"Bulk index error: {e}")
            for error in e.errors:
                logger.error(f"Failed document: {error}")
            state.increment_failed('genres', len(genres))
            raise

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    def load_movies(self, movies: list[dict[str, Any]]):
        state = State()
        sanitized_movies = []
        for items in movies:
            for movie in items:
                try:
                    # Create a new dict with only the fields we want to index
                    sanitized_movie = {
                        "id": movie["id"],
                        "imdb_rating": movie.get("rating", None),
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
                                # Default value for imdb_rating
                                sanitized_movie[key] = 0.0
                            else:
                                sanitized_movie[key] = (
                                    [] if key.endswith("_names") or
                                    key in [
                                        "genres",
                                        "actors",
                                        "directors",
                                        "writers"
                                    ]
                                    else ""
                                )

                    sanitized_movies.append(sanitized_movie)
                except Exception as e:
                    logger.error(
                        f"Error sanitizing movie: {movie}, error: {e}"
                    )

            actions = [
                {"_index": "movies", "_id": movie["id"], "_source": movie}
                for movie in sanitized_movies
            ]

            try:
                helpers.bulk(self.es, actions)
                state.increment_processed('movies', len(items))
                stats = state.get_statistics('movies')
                logger.info(
                    f"Successfully processed {len(items)} movies. "
                    f"Total processed: {stats['total_processed']}")
            except helpers.BulkIndexError as e:
                logger.error(f"Bulk index error: {e}")
                for error in e.errors:
                    logger.error(f"Failed document: {error}")
                state.increment_failed('movies', len(items))
                raise

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    def load_persons(self, pages: list[dict[str, Any]]):
        state = State()
        sanitized_persons = []
        for page in pages:
            for person in page:
                try:
                    # Create a new dict with only the fields we want to index
                    sanitized_movie = {
                        "id": person["id"],
                        "full_name": person.get("full_name", None),
                        "films": person.get("films", [])
                    }

                    sanitized_persons.append(sanitized_movie)
                except Exception as e:
                    logger.error(
                        f"Error sanitizing movie: {person}, error: {e}"
                    )

            actions = [
                {"_index": "persons", "_id": person["id"], "_source": person}
                for person in sanitized_persons
            ]

            try:
                helpers.bulk(self.es, actions)
                state.increment_processed('persons', len(page))
                stats = state.get_statistics('persons')
                logger.info(
                    f"Successfully processed {len(page)} persons. "
                    f"Total processed: {stats['total_processed']}")
            except helpers.BulkIndexError as e:
                logger.error(f"Bulk index error: {e}")
                for error in e.errors:
                    logger.error(f"Failed document: {error}")
                state.increment_failed('persons', len(page))
                raise
