import datetime as dt
import os

from dotenv import load_dotenv

load_dotenv()

dsl = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
}
DB_READ_LIMIT = 100
START_DATE = dt.datetime.fromisoformat('2000-01-01')
LOG_SIZE = 1048576
LOG_FILE_NAME = 'etl.log'
DEFAULT_INDEX = 'movies'
DELAY = 30
ES_HOST = os.getenv('ES_HOST')
ES_PORT = os.getenv('ES_PORT')
ES_PROTOCOL = os.getenv('ES_PROTOCOL')
ES_CONN = f'{ES_PROTOCOL}://{ES_HOST}:{ES_PORT}'
REDIS_HOST = os.getenv('REDIS_HOST')
STORAGE_REDIS = 1
STR_TIME_NOW = str(dt.datetime.now(dt.timezone.utc))
STATE_NAME = 'etl'
STATES = [
    {'name': 'person', 'date': '',
     'key_field': 'person_id', 'offset': 0,
     'table_name': 'person_film_work'},
    {'name': 'genre', 'date': '',
     'key_field': 'genre_id', 'offset': 0,
     'table_name': 'genre_film_work'},
    {'name': 'film_work', 'date': '',
     'key_field': 'id', 'offset': 0,
     'table_name': 'film_work', 'init': 0},
]
