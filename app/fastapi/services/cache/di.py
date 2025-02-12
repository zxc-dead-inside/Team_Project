from db.redis import redis_connector
from services.cache.film_cache import FilmCacheService
from services.cache.genre_cache import GenreCacheService
from services.cache.person_cache import PersonCacheService
from services.cache.redis_cache import RedisCacheStorage


def get_film_cache_service() -> FilmCacheService:
    return FilmCacheService(RedisCacheStorage(redis_connector.get_redis()))

def get_genre_cache_service() -> GenreCacheService:
    return GenreCacheService(RedisCacheStorage(redis_connector.get_redis()))

def get_person_cache_service() -> PersonCacheService:
    return PersonCacheService(RedisCacheStorage(redis_connector.get_redis()))