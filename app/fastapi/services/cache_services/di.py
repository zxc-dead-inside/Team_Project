from services.cache.di import get_cache_storage
from services.cache_services.film_cache_service import FilmCacheService
from services.cache_services.genre_cache_service import GenreCacheService
from services.cache_services.person_cache_service import PersonCacheService


def get_film_cache_service() -> FilmCacheService:
    return FilmCacheService(get_cache_storage())


def get_genre_cache_service() -> GenreCacheService:
    return GenreCacheService(get_cache_storage())


def get_person_cache_service() -> PersonCacheService:
    return PersonCacheService(get_cache_storage())
