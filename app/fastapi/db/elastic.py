from elasticsearch import (
    AsyncElasticsearch,
    ConnectionError,
    ConnectionTimeout,
    TransportError,
)

from core.config import settings
from core.decorators.retry import exponential_backoff



es: AsyncElasticsearch | None = None

# Функция понадобится при внедрении зависимостей
async def get_elastic() -> AsyncElasticsearch:
    return es


class EsConnector:

    def __init__(self):
        self._es: AsyncElasticsearch | None = None

    @property
    def es_url(self) -> str:
        return (
            f"http://{settings.elasticsearch_host}:"
            f"{settings.elasticsearch_port}"
        )

    @exponential_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=5.0,
        exceptions=(ConnectionError, ConnectionTimeout, TransportError)
    )
    async def connect(self):
        if self._es is None:
            self._es = AsyncElasticsearch(
                hosts=[
                    f"http://{settings.elasticsearch_host}:"
                    f"{settings.elasticsearch_port}"
                ],
                basic_auth=(
                    settings.elasticsearch_username,
                    settings.elasticsearch_password
                )
                if settings.elasticsearch_username
                else None
            )

    async def disconnect(self):
        if self._es:
            await self._es.close()
            self._es = None

    def get_es(self) -> AsyncElasticsearch:
        if self._es is None:
            raise RuntimeError(
                "Elasticsearch connection has not been established.")
        return self._es


es_connector = EsConnector()
