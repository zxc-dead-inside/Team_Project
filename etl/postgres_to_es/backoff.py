import logging
import time
from functools import wraps

from elastic_transport import ConnectionError
import psycopg
from psycopg import ClientCursor
from psycopg.rows import dict_row

from settings import dsl


logger = logging.getLogger(__name__)


def check_connection():
    """Восстанавлиает соединение с БД."""

    def wrap(func):
        @wraps(func)
        def inner(self, *args, **kwargs):
            try:
                if self.pg_conn.broken:
                    logger.debug(
                        'Попытка восстановить соединение с БД.')
                    self.pg_conn.rollback()
                    self.pg_conn = psycopg.connect(
                        **dsl, row_factory=dict_row,
                        cursor_factory=ClientCursor)
                    self.pg_conn.rollback()
                    self.cursor = self.pg_conn.cursor()
            except psycopg.OperationalError as err:
                logger.debug(
                    'При восстановлении соединения возникла ошибка.',
                    exc_info=err)
            logger.debug('Соединение с БД установлено.')
            return func(self, *args, **kwargs)
        return inner
    return wrap


def backoff(start_sleep_time=0.1, factor=2, border_sleep_time=10):
    """
    Функция для повторного выполнения функции через некоторое время,
    если возникла ошибка. Использует наивный экспоненциальный рост
    времени повтора (factor) до граничного времени ожидания
    (border_sleep_time)

    Формула:
        t = start_sleep_time * (factor ^ n), если t < border_sleep_time
        t = border_sleep_time, иначе
    :param start_sleep_time: начальное время ожидания
    :param factor: во сколько раз нужно увеличивать время ожидания на
        каждой итерации
    :param border_sleep_time: максимальное время ожидания
    :return: результат выполнения функции
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            def set_delay(count: int, delay: int) -> float:
                if delay < border_sleep_time:
                    delay = start_sleep_time * (factor ** (count/2))
                else:
                    delay = border_sleep_time
                return delay

            delay = 0
            count = 1
            while True:
                try:
                    delay = set_delay(count, delay)
                    result = func(*args, **kwargs)
                    return result
                except psycopg.OperationalError as err:
                    # count += 1
                    logger.debug(
                        f'Попытка соединения {count} завершилась '
                        'ошибкой', exc_info=err)

                    # if delay < border_sleep_time:
                    #     delay = start_sleep_time * (
                    #         factor ** (count/2))
                    # else:
                    #     delay = border_sleep_time
                    logger.debug(
                        'Следующая попытка через '
                        f'{delay:.2f} секунд.')
                    time.sleep(delay)

                except ConnectionError as err:
                    logger.debug(
                        'Ошибка подключения к ES.', exc_info=err)
                    logger.debug(
                        'Следующая попытка через '
                        f'{delay:.2f} секунд.')
                    time.sleep(delay)
                except Exception as err:
                    logger.debug(
                        "Непредвиденная ошибка.", exc_info=err)
                    time.sleep(delay)
                finally:
                    count += 1
        return inner
    return func_wrapper
