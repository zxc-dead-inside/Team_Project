import logging
import sys
from contextlib import closing
from logging.handlers import RotatingFileHandler
from time import sleep

import psycopg
from elasticsearch import Elasticsearch
from psycopg import ClientCursor, connection as _connection
from psycopg.rows import dict_row
from redis import Redis

from backoff import backoff
from db_loader import PostgresLoader
from etl_func import filmwork_changes, film_work_populate
from index import INDEX_MAPPINGS, INDEX_SETTINGS
from send_to_es import SendToEs
from settings import (
    DEFAULT_INDEX, DELAY, dsl, ES_CONN, LOG_FILE_NAME,
    LOG_SIZE, REDIS_HOST, STATES, STORAGE_REDIS)
from state import RedisStorage, State
from transform import Transform


log_path = LOG_FILE_NAME
file_handler = RotatingFileHandler(
    log_path, maxBytes=LOG_SIZE, backupCount=3)
stream_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, stream_handler],
    format='%(asctime)s  [%(levelname)s] %(message)s')


def etl_run(pg_conn: _connection):
    """Основой процесс ETL."""

    postgres_loader = PostgresLoader(pg_conn)
    transform = Transform()
    send_to_es = SendToEs(Elasticsearch(hosts=ES_CONN))
    state = State(
        RedisStorage(Redis(host=REDIS_HOST, db=STORAGE_REDIS)))

    # Проверяем наличие индекса и создаем его, если его нет.
    if not send_to_es.check_index_exists(DEFAULT_INDEX):
        logging.debug(f'Индекс "{DEFAULT_INDEX}" не существует.')
        logging.debug(
            f'Индекс "{DEFAULT_INDEX}" будет создан автоматически.')
        send_to_es.create_index(
            DEFAULT_INDEX, INDEX_MAPPINGS, INDEX_SETTINGS)

    offset = 0
    while True:
        movies_state = state.get_state('movies')
        logging.debug(f'Прочитано состояние ETL: {movies_state}')

        if not movies_state:
            logging.debug(
                'Сохраненное состояние не найдено. Начинается '
                'процесс инициаизации индекса, в индекс будут '
                'перенесены все данные из базы.')
            movies_state = state.set_init(STATES)
            logging.debug(f'Состояние инициализации: {movies_state}')
            state.set_state('movies', movies_state)

        if state.get_init(movies_state):
            offset = state.get_param(
                movies_state, 'film_work', 'offset')
            film_work_populate(
                postgres_loader, transform, send_to_es, state,
                movies_state, offset)

        if not movies_state:
            continue

        # Здесь начинается обычная работа ETL.
        logging.debug('Начало процесса ETL.')
        logging.info(movies_state)

        filmwork_changes(
            postgres_loader, transform, send_to_es, state,
            movies_state)

        logging.info(f'Пауза {DELAY} секунд.')
        sleep(DELAY)


@backoff()
def db_connect():
    """Подключение к БД."""

    with closing(
        psycopg.connect(
            **dsl, row_factory=dict_row,
            cursor_factory=ClientCursor)) as pg_conn:
        etl_run(pg_conn)


if __name__ == '__main__':
    db_connect()
