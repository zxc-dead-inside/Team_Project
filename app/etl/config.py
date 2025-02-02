from pathlib import Path
from typing import Any, Dict

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQL_HOST: str
    SQL_PORT: int

    # Elasticsearch settings
    ELASTICSEARCH_HOST: str
    ELASTICSEARCH_PORT: int

    # ETL settings
    BATCH_SIZE: int = 100
    STATE_FILE_PATH: Path = Path("state/etl_state.json")

    SLEEP_TIME: int = 60
    BASE_DATE: str = "1970-01-01T00:00:00"
    INDECIES: list = ['movies', 'genres', 'persons']

    @property
    def postgres_dsn(self) -> str:
        return "postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}".format(
            USER=self.POSTGRES_USER,
            PASSWORD=self.POSTGRES_PASSWORD,
            HOST=self.SQL_HOST,
            PORT=self.SQL_PORT,
            DBNAME=self.POSTGRES_DB
        )

    class Config:
        env_file = ".env"


class ESIndexSettings(BaseSettings):
    movies_settings:  Dict[str, Any] = {
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
    }

    movies_mappings: Dict[str, Any] = {
        "dynamic": "strict",
        "properties": {
            "id": {
                "type": "keyword"
            },
            "imdb_rating": {
                "type": "float"
            },
            "genres": {
                "type": "keyword"
            },
            "title": {
                "type": "text",
                "analyzer": "ru_en",
                "fields": {
                    "raw": {
                        "type": "keyword"
                    }
                }
            },
            "description": {
                "type": "text",
                "analyzer": "ru_en"
            },
            "directors_names": {
                "type": "text",
                "analyzer": "ru_en"
            },
            "actors_names": {
                "type": "text",
                "analyzer": "ru_en"
            },
            "writers_names": {
                "type": "text",
                "analyzer": "ru_en"
            },
            "directors": {
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
                    "id": {
                        "type": "keyword"
                    },
                    "name": {
                        "type": "text",
                        "analyzer": "ru_en"
                    }
                }
            },
            "writers": {
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
            }
        }
    }

    genres_mappings: Dict[str, Any] = {
        "dynamic": "strict",
        "properties": {
            "id": {
                "type": "keyword"
            },
            "name": {
                "type": "keyword"
            }
        }
    }

    persons_settings: Dict[str, Any] = {
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
        }
    }

    persons_mapping: Dict[str, Any] = {
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


es_indices_settings = ESIndexSettings()
