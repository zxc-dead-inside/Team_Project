import json
import logging
from uuid import UUID

import redis.asyncio as redis

from src.core.logger import setup_logging

setup_logging()


class UUIDEncoder(json.JSONEncoder):
    """JSON Encoder that handles UUID serialization."""

    def default(self, obj):
        """Convert UUID objects to strings."""
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class RedisService:

    def __init__(self, redis_url: str, default_ttl: int = 3600):

        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = redis.from_url(redis_url)
    
    async def exists(self, key: str) -> bool:
        """Return True if key exists or False if does not"""

        return self.exists(key)  # type:ignore

    async def get(self, key: str) -> str | None:
        """Get a value from Redis by key."""
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logging.error(f"Error getting key {key} from Redis: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Set a key-value pair in Redis with TTL."""
        try:
            serialized = json.dumps(value, cls=UUIDEncoder)
            await self.redis_client.set(
                key, serialized, ex=ttl if ttl is not None else self.default_ttl
            )
            return True
        except Exception as e:
            logging.error(f"Error setting key {key} in Redis: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from Redis."""
        try:
            return await self.redis_client.delete(*keys)
        except Exception as e:
            logging.error(f"Error deleting keys {keys} from Redis: {e}")
            return 0
    
    async def incr(self, key: str) -> bool:
        """Увеличивает значение на единицу."""
        try:
            await self.redis_client.incr(key)
            return True
        except Exception as e:
            logging.error(f"Error incrementing {key}", exc_info=e)
            return False
    
    async def hset(self, name: str, field: str, value: str) -> bool:
        """Устанавливает хэш."""
        try:
             await self.redis_client.hset(name, field, value)
             return True
        except Exception as e:
            logging.error(f"Error writing field {field}", exc_info=e)
            return False
    
    async def hdel(self, name: str, field: str) -> bool:
        """Удаляет хэш."""
        try:
            await self.redis_client.hdel(name, field)
            return True
        except Exception as e:
            logging.error(f"Error deleting field {field}")
            return False
    
    async def hget(self, name: str, field: str) -> str | None:
        """Получает хэш."""
        try:
            return self.redis_client.hget(name, field)
        except Exception as e:
            logging.error(f"Error getting field {field}")
            return None