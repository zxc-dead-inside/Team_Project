from services.search_platform.di import get_search_platform
from services.search_services.film_search_service import FilmSearchService
from services.search_services.genre_search_service import GenreSearchSerivce
from services.search_services.person_search_service import PersonSearchService


def get_film_search_platform_service() -> FilmSearchService:
    return FilmSearchService(get_search_platform())


def get_genre_search_platform_service() -> GenreSearchSerivce:
    return GenreSearchSerivce(get_search_platform())


def get_person_search_platform_service() -> PersonSearchService:
    return PersonSearchService(get_search_platform())
