import logging
from typing import Dict, List

import psycopg

from db_loader import PostgresLoader
from queries import queries
from transform import Transform
from send_to_es import SendToEs
from settings import DB_READ_LIMIT
from state import State
from structs import BaseDataSet, FilmWorkChanged, FilmWorkPopulate
from utils import get_data_gen, get_time, get_uuid_str


def film_work_populate(
        pg_loader: PostgresLoader, transform: Transform,
        send_to_es: SendToEs, state: State,
        movies_state: List[Dict[str, str]], offset: int):
    """Полностью заполняет индекс movies."""

    limit = DB_READ_LIMIT

    while True:
        try:
            query = queries.etl_init(offset, limit)
            film_works = pg_loader.get_data(
                FilmWorkPopulate, query)

        except psycopg.errors.OperationalError:
            pass
        bulk = transform.prepare(
            film_works, 'film_work', init=True)

        if not bulk:
            logging.debug(
                'Все данные были перенесены, процесс '
                'инициализации завершен.')
            movies_state = state.set_param_bulk(
                movies_state, 'date', get_time())
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


def filmwork_changes(
        pg_loader: PostgresLoader, transform: Transform,
        send_to_es: SendToEs, state: State,
        movies_state: List[Dict[str, str]]):
    """
    Отслеживает изменившиеся данные в film_work, genre, person и
    обновляет индекс movies.
    """

    limit = DB_READ_LIMIT

    for item in movies_state:
        logging.debug(f'Обрабатываем таблицу: {item["name"]}')
        offset = state.get_param(
            movies_state, item['name'], 'offset')
        if item['name'] != 'film_work':
            while True:
                query = queries.get_id_by_date(
                    item['date'], item['name'], offset, limit)
                changed_id = pg_loader.get_data(
                    BaseDataSet, query)

                try:
                    data = get_data_gen(changed_id)
                    if len(data) == 0:
                        logging.debug(
                            'Нет данных удовлетворяющих условию.')
                        break
                    ids = get_uuid_str(data)
                    offset += limit
                except psycopg.OperationalError as err:
                    logging.debug(
                        'Ошибка подключения к базе',
                        exc_info=err)

                logging.info(
                    f'Список id измененных элменетов {ids} '
                    f'таблицы {item["name"]}')
                logging.debug(
                    'Получения писка id film_work, требующих '
                    'обновления в es.')
                fw_ids = pg_loader.get_fw_by_id(
                    ids, item['table_name'], item['key_field'])
                for ids in fw_ids:
                    logging.debug(
                        'Получение нужных полей film_work.')
                    fw = pg_loader.get_fw(ids, item['name'])
                    fw = get_data_gen(fw)
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
            movies_state = state.set_param(
                movies_state, item['name'], 'date', get_time())
            logging.debug(f'Новое состояние: {movies_state}')
            state.set_state('movies', movies_state)

        elif item['name'] == 'film_work':
            while True:
                query = queries.get_changed_fw(
                    item['date'], offset, limit)
                changed_fw = pg_loader.get_data(
                    FilmWorkChanged, query)

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
            logging.debug(f'Таблица: {item["name"]} обработана')
            movies_state = state.flush_offset(movies_state)
            movies_state = state.set_param(
                movies_state, item['name'], 'date', get_time())
            logging.debug(f'Новое состояние: {movies_state}')
            state.set_state('movies', movies_state)
