import logging
from typing import Any, Dict, List

from elasticsearch import Elasticsearch

from backoff import backoff

loggger = logging.getLogger(__name__)


class SendToEs:

    def __init__(self, es_conn: Elasticsearch):
        self.es_conn = es_conn

    @backoff()
    def check_index_exists(self, name: str = 'movies') -> bool:
        """Проверяет наличие указанного индекса в es."""

        return self.es_conn.indices.exists(index=name)

    def create_index(self, name, mappings, settings):
        loggger.debug(f'Создается индекс "{name}".')
        try:
            self.es_conn.indices.create(
                index=name, mappings=mappings, settings=settings)
        except Exception as err:
            loggger.error(
                'При создании индекса произошла ошибка.',
                exc_info=err)
        loggger.debug(f'Индекс "{name}" успешно создан.')

    @backoff()
    def send_bulk(self, bulk: List[Dict[str, Any]]):
        """Отправляет пачку данных в es."""

        loggger.debug('Загрузка данных в es.')
        try:
            response = self.es_conn.bulk(
                operations=bulk,
                filter_path='items.*.error')
            loggger.debug(response)
        except Exception as err:
            loggger.error('Произошла ошибка.', exc_info=err)
