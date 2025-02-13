from fastapi import Depends
from functools import lru_cache

from services.person import PersonService
from services.genre import GenreService
from services.film import FilmService

from services.cache.di import get_person_cache_service
from services.cache.di import get_genre_cache_service
from services.cache.di import get_film_cache_service

from services.cache.person_cache import PersonCacheService
from services.cache.genre_cache import GenreCacheService
from services.cache.film_cache import FilmCacheService

from services.search_platform.di import get_person_search_platform_service
from services.search_platform.di import get_genre_search_platform_service
from services.search_platform.di import get_film_search_platform_service

from services.search_platform.person_search_platform import PersonSearchService
from services.search_platform.genre_search_platform import GenreSearchSerivce
from services.search_platform.film_search_platform import FilmSearchService


@lru_cache()
def get_person_service(
        cache_service: PersonCacheService = Depends(get_person_cache_service),
        elastic: PersonSearchService = Depends(
            get_person_search_platform_service
        )
) -> PersonService:
    return PersonService(cache_service, elastic)

@lru_cache()
def get_genre_service(
    cache_service: GenreCacheService = Depends(get_genre_cache_service),
    search_platform: GenreSearchSerivce = Depends(
        get_genre_search_platform_service
    )
) -> GenreService:
    return GenreService(
        cache_service=cache_service,
        search_platform=search_platform
    )

@lru_cache()
def get_film_service(
        cache_service: FilmCacheService = Depends(get_film_cache_service),
        search_platform: FilmSearchService = Depends(
            get_film_search_platform_service
        )
) -> FilmService:
    return FilmService(cache_service, search_platform)