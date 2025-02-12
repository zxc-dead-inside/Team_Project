from db.elastic import es_connector
from services.search_platform.es import EsSearchPlatform
from services.search_platform.film_sp import FilmSearchService
from services.search_platform.genre_sp import GenreSearchSerivce
from services.search_platform.person_sp import PersonSearchService


def get_film_sp_service() -> FilmSearchService:
    return FilmSearchService(EsSearchPlatform(es_connector.get_es()))
def get_genre_sp_service() -> GenreSearchSerivce:
    return GenreSearchSerivce(EsSearchPlatform(es_connector.get_es()))
def get_person_sp_service() -> PersonSearchService:
    return PersonSearchService(EsSearchPlatform(es_connector.get_es()))