from db.redis import redis_connector
from services.cache.redis_cache import RedisCacheStorage


def get_cache_storage() -> RedisCacheStorage:
    return RedisCacheStorage(redis_connector.get_redis())