from db.elastic import es_connector

from services.search_platform.film_es import FilmSearchService
from services.search_platform.es import EsSearchPlatform

def get_film_sp_service() -> FilmSearchService:
    return FilmSearchService(EsSearchPlatform(es_connector.get_es()))