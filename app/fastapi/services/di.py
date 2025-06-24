from functools import lru_cache

from services.cache_services.di import (
    get_film_cache_service,
    get_genre_cache_service,
    get_person_cache_service,
)
from services.cache_services.film_cache_service import FilmCacheService
from services.cache_services.genre_cache_service import GenreCacheService
from services.cache_services.person_cache_service import PersonCacheService
from services.film import FilmService
from services.genre import GenreService
from services.person import PersonService
from services.search_services.di import (
    get_film_search_platform_service,
    get_genre_search_platform_service,
    get_person_search_platform_service,
)
from services.search_services.film_search_service import FilmSearchService
from services.search_services.genre_search_service import GenreSearchSerivce
from services.search_services.person_search_service import PersonSearchService

from fastapi import Depends


@lru_cache
def get_person_service(
    cache_service: PersonCacheService = Depends(get_person_cache_service),
    elastic: PersonSearchService = Depends(get_person_search_platform_service),
) -> PersonService:
    return PersonService(cache_service, elastic)


@lru_cache
def get_genre_service(
    cache_service: GenreCacheService = Depends(get_genre_cache_service),
    search_platform: GenreSearchSerivce = Depends(get_genre_search_platform_service),
) -> GenreService:
    return GenreService(cache_service=cache_service, search_platform=search_platform)


@lru_cache
def get_film_service(
    cache_service: FilmCacheService = Depends(get_film_cache_service),
    search_platform: FilmSearchService = Depends(get_film_search_platform_service),
) -> FilmService:
    return FilmService(cache_service, search_platform)
