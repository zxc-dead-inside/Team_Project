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
from index import INDEX_MAPPINGS, INDEX_SETTINGS
from queries import queries
from send_to_es import SendToEs
from settings import (
    DB_READ_LIMIT, DEFAULT_INDEX, DELAY, dsl, ES_CONN, LOG_FILE_NAME,
    LOG_SIZE, REDIS_HOST, STATES, STORAGE_REDIS, STR_TIME_NOW)
from state import RedisStorage, State
from structs import data_structs
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
    limit = DB_READ_LIMIT
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
            while True:
                try:
                    film_works = postgres_loader.get_data(
                        data_structs.get_film_work_init,
                        queries.etl_init(offset, limit))
                except psycopg.errors.OperationalError:
                    pass
                bulk = transform.prepare(
                    film_works, 'film_work', init=True)

                if not bulk:
                    logging.debug(
                        'Все данные были перенесены, процесс '
                        'инициализации завершен.')
                    movies_state = state.set_param_bulk(
                        movies_state, 'date', STR_TIME_NOW)
                    movies_state = state.flush_offset(movies_state)
                    movies_state = state.set_init(movies_state)
                    logging.debug(f'Новое состояние: {movies_state}')
                    state.set_state('movies', movies_state)
                    break

                send_to_es.send_bulk(bulk)
                offset += limit
                movies_state = state.set_param(
                    movies_state, 'film_work', 'offset', offset)
                logging.debug(f'Новое состояние: {movies_state}')
                state.set_state('movies', movies_state)

        if not movies_state:
            continue

        # Здесь начинается обычная работа ETL.
        logging.debug('Начало процесса ETL.')
        logging.info(movies_state)

        for item in movies_state:
            logging.debug(f'Обрабатываем таблицу: {item["name"]}')
            offset = state.get_param(
                movies_state, item['name'], 'offset')
            if item['name'] != 'film_work':
                while True:
                    changed_id = postgres_loader.get_data(
                        data_structs.base_dataset,
                        queries.get_id_by_date(
                            item['date'], item['name'],
                            offset, limit))
                    try:
                        for data in changed_id:
                            if len(data) > 0:
                                ids = [element.id for element in data]
                                if len(ids) == 1:
                                    ids = f"('{ids[0]}')"
                                else:
                                    ids = tuple(ids)
                        offset += limit
                    except psycopg.OperationalError as err:
                        logging.debug('Ошибка', exc_info=err)
                    if len(data) == 0:
                        logging.debug(
                            'Нет данных удовлетворяющих условию.')
                        break
                    logging.info(
                        f'Список id измененных элменетов {ids} '
                        f'таблицы {item["name"]}')

                    fw_ids = postgres_loader.get_fw_by_id(
                        ids, item['table_name'],
                        item['key_field']
                    )
                    for ids in fw_ids:
                        fw = postgres_loader.get_fw(
                            ids, item['name'])
                        fw = [item for item in fw]
                        bulk = transform.prepare(fw, item['name'])
                        send_to_es.send_bulk(bulk)
                    else:
                        movies_state = state.set_param(
                                movies_state, item['name'],
                                'offset', offset)
                        logging.debug(
                                f'Новое состояние: {movies_state}')
                        state.set_state('movies', movies_state)

                logging.debug(f'Таблица: {item["name"]} обработана')
                movies_state = state.flush_offset(movies_state)
                logging.debug(f'Новое состояние: {movies_state}')
                state.set_state('movies', movies_state)

            elif item['name'] == 'film_work':
                while True:
                    changed_fw = postgres_loader.get_data(
                        data_structs.get_film_work_changed,
                        queries.get_changed_fw(
                            item['date'], offset, limit))
                    bulk = transform.prepare(changed_fw, 'film_work')
                    offset += limit
                    if not bulk:
                        logging.debug(
                            f'Данные в таблице: {item["name"]} '
                            'были обработаны.')
                        movies_state = state.flush_offset(
                            movies_state)
                        logging.debug(
                            f'Новое состояние: {movies_state}')
                        state.set_state('movies', movies_state)
                        break
                    send_to_es.send_bulk(bulk)
                    movies_state = state.set_param(
                        movies_state, 'film_work', 'offset',
                        offset)
                    logging.debug(
                        f'Новое состояние: {movies_state}')
                    state.set_state('movies', movies_state)
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
