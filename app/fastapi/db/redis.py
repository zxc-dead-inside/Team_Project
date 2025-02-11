import redis.asyncio as aioredis
from redis.asyncio import Redis
from core.config import settings


redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_cache_db}"

class RedisConnector:

    def __init__(self):
        self._redis: Redis | None = None
    async def connect(self):
        if self._redis is None:
            self._redis = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def disconnect(self):
        if self._redis:
            await self._redis.close()
            self._redis = None

    def get_redis(self) -> Redis:
        if self._redis is None:
            raise RuntimeError(
                "Redis connection has not been established.")
        return self._redis


redis_connector = RedisConnector()