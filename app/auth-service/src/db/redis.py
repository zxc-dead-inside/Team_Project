import redis.asyncio as aioredis
from redis.asyncio import Redis
from src.core.decorators.retry import exponential_backoff


class RedisConnector:

    def __init__(self, redis_url):
        self._redis: Redis | None = None
        self.redis_url = redis_url

    @exponential_backoff.network_errors(
        additional_exceptions=(aioredis.RedisError, aioredis.ConnectionError),
        base=0.5,
    )
    async def connect(self):
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url,
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

_redis_instance: RedisConnector | None = None

def get_redis(redis_url):
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = RedisConnector(redis_url)
    return _redis_instance

def get_redis_session():
    return _redis_instance