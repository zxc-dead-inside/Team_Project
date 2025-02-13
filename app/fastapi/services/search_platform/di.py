from db.elastic import es_connector
from services.search_platform.elasticsearch_search_platform import EsSearchPlatform
from services.search_platform.film_search_platform import FilmSearchService
from services.search_platform.genre_search_platform import GenreSearchSerivce
from services.search_platform.person_search_platform import PersonSearchService


def get_film_search_platform_service() -> FilmSearchService:
    return FilmSearchService(EsSearchPlatform(es_connector.get_es()))

def get_genre_search_platform_service() -> GenreSearchSerivce:
    return GenreSearchSerivce(EsSearchPlatform(es_connector.get_es()))

def get_person_search_platform_service() -> PersonSearchService:
    return PersonSearchService(EsSearchPlatform(es_connector.get_es()))