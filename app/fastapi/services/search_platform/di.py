from db.elastic import es_connector
from services.search_platform.elasticsearch_search_platform import EsSearchPlatform


def get_search_platform() -> EsSearchPlatform:
    return EsSearchPlatform(es_connector.get_es())