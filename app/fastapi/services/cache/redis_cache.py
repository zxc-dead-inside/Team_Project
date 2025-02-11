from redis.asyncio import Redis

from services.cache.base import AbstractCacheStorage

class RedisCacheStorage(AbstractCacheStorage):
    """Class for Redis cache storage."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, ttl: int) -> None:
        await self.redis.set(key, value, ex=ttl)
