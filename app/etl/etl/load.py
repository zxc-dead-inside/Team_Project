from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError
from elasticsearch.exceptions import ConnectionError, TransportError, RequestError
import backoff
from core.logger import setup_logger

logger = setup_logger("load")


class ElasticsearchClient:
    def __init__(self, es_host: str, index: str, index_body: dict):
        self.es_host = es_host
        self.index = index
        self.index_body = index_body
        self.es = None
        self.connect()
        self.ensure_index_exists()

    @backoff.on_exception(
        backoff.expo,
        (ConnectionError, TransportError),
        max_time=60
    )
    def connect(self):
        logger.info(f"Подключение к Elasticsearch на {self.es_host}...")
        self.es = Elasticsearch([self.es_host])
        if not self.es.ping():
            raise ConnectionError("Elasticsearch недоступен")
        logger.info("Подключение к Elasticsearch установлено.")

    def ensure_index_exists(self):
        if not self.es.indices.exists(index=self.index):
            self.es.indices.create(index=self.index, body=self.index_body)
            logger.info(f"Индекс '{self.index}' создан.")
        else:
            logger.info(f"Индекс '{self.index}' уже существует.")

    def index_data(self, data: list[dict]):
        actions = []
        for doc in data:
            action = {
                "_op_type": "index",
                "_index": self.index,
                "_id": doc["id"],
                "_source": doc
            }
            actions.append(action)

        try:
            if actions:
                success, failed = bulk(self.es, actions)
                logger.info(f"Успешно проиндексировано {success} документов.")
                if failed:
                    logger.error(
                        f"Не удалось проиндексировать {failed} документов.")
        except (ConnectionError, TransportError) as e:
            logger.error(f"Ошибка при индексации данных: {e}")
        except BulkIndexError as e:
            logger.error(f"Ошибка пакетной индексации: {e}")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при индексации данных: {e}")

    def close(self):
        if self.es:
            self.es.transport.close()
            logger.info("Соединение с Elasticsearch закрыто.")
