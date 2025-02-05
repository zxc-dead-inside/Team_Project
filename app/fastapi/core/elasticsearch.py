from elasticsearch import AsyncElasticsearch

from .config import settings


es_client = AsyncElasticsearch(
    hosts=[
        f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
    ],
    basic_auth=(
        settings.ELASTICSEARCH_USERNAME,
        settings.ELASTICSEARCH_PASSWORD
    )
    if settings.ELASTICSEARCH_USERNAME
    else None
)
