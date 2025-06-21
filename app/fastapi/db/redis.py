import redis.asyncio as aioredis
from core.config import settings
from core.decorators.retry import exponential_backoff
from redis.asyncio import Redis


class RedisConnector:

    def __init__(self):
        self._redis: Redis | None = None

    @property
    def redis_url(self) -> str:
        return (
            f"redis://{settings.redis_host}:"
            f"{settings.redis_port}/"
            f"{settings.redis_cache_db}"
        )

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


redis_connector = RedisConnector()