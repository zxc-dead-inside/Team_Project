from typing import Any
from pydantic_settings import BaseSettings


MOVIES_MAPPING = {
    "settings": {
        "analysis": {
            "filter": {
                "ru_stop": {"type": "stop", "stopwords": "_russian_"},
                "en_stop": {"type": "stop", "stopwords": "_english_"},
                "ru_stemmer": {"type": "stemmer", "language": "russian"},
                "en_stemmer": {"type": "stemmer", "language": "english"},
            },
            "analyzer": {
                "ru_en": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "ru_stop", "en_stop", "ru_stemmer", "en_stemmer"],
                }
            }
        }
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "imdb_rating": {"type": "float"},
            "genres": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"},  # <-- Используем ru_en
                },
            },
            "title": {
                "type": "text",
                "analyzer": "ru_en",
                "fields": {"raw": {"type": "keyword"}},
            },
            "description": {"type": "text", "analyzer": "ru_en"},
            "directors_names": {"type": "text", "analyzer": "ru_en"},
            "actors_names": {"type": "text", "analyzer": "ru_en"},
            "writers_names": {"type": "text", "analyzer": "ru_en"},
            "directors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "actors": {
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

PERSONS_MAPPINGS = {
    "settings": {
        "refresh_interval": "1s",
        "analysis": {
            "filter": {
                "english_stop": {"type": "stop", "stopwords": "_english_"},
                "english_stemmer": {"type": "stemmer", "language": "english"},
                "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                "russian_stemmer": {"type": "stemmer", "language": "russian"}
            },
            "analyzer": {
                "ru_en": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "english_stop", "english_stemmer", "russian_stop", "russian_stemmer"
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

GENRE_MAPPING = {
    "mappings": {
        "properties": {
            "id": {
                "type": "keyword"
            },
            "name": {
                "type": "keyword"
            }
        }
    }
}


class ESIndicesSettings(BaseSettings):
    movies_settings:  dict[str, Any] = {
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

    movies_mappings: dict[str, Any] = {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "imdb_rating": {"type": "float"},
            "genres": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text","analyzer": "ru_en"}
                }
            },
            "title": {
                "type": "text",
                "analyzer": "ru_en",
                "fields": {"raw": {"type": "keyword"}}
            },
            "description": {"type": "text","analyzer": "ru_en"},
            "directors_names": {"type": "text","analyzer": "ru_en"},
            "actors_names": {"type": "text","analyzer": "ru_en"},
            "writers_names": {"type": "text","analyzer": "ru_en"},
            "directors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text","analyzer": "ru_en"}
                }
            },
            "actors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"}
                }
            },
            "writers": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text","analyzer": "ru_en"                    }
                }
            }
        }
    }

    persons_settings: dict[str, Any] = {
            "refresh_interval": "1s",
            "analysis": {
                "filter": {
                    "english_stop": {"type": "stop", "stopwords": "_english_"},
                    "english_stemmer": {"type": "stemmer", "language": "english"},
                    "english_possessive_stemmer": {"type": "stemmer", "language": "possessive_english"},
                    "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                    "russian_stemmer": {"type": "stemmer", "language": "russian"}
                },
                "analyzer": {
                    "ru_en": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "english_stop", "english_stemmer", "english_possessive_stemmer", "russian_stop", "russian_stemmer"]
                    }
                }
            }
    }

    persons_mapping: dict[str, Any] = {
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


es_indices_settings = ESIndicesSettings()
