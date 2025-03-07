"""Redis service for caching."""

import json
import logging
from typing import TypeVar
from uuid import UUID

import redis.asyncio as redis
from pydantic import BaseModel


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class UUIDEncoder(json.JSONEncoder):
    """JSON Encoder that handles UUID serialization."""

    def default(self, obj):
        """Convert UUID objects to strings."""
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


async def check_redis_connection(redis_url: str) -> bool:
    """
    Check if the Redis connection is healthy.

    Args:
        redis_url: Redis URL to connect to

    Returns:
        bool: True if the connection is healthy, False otherwise
    """
    client = redis.from_url(redis_url)
    try:
        await client.ping()
        await client.close()
        return True
    except Exception:
        await client.close()
        return False


class RedisService:
    """Service for Redis caching operations."""

    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """Initialize the Redis service.

        Args:
            redis_url: URL for Redis connection
            default_ttl: Default cache TTL in seconds (1 hour default)
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = redis.from_url(redis_url)

    async def get(self, key: str) -> str | None:
        """Get a value from Redis by key."""
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
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
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from Redis."""
        try:
            return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting keys {keys} from Redis: {e}")
            return 0

    async def get_model(self, key: str, model_class: type[T]) -> T | None:
        """Get a Pydantic model from Redis by key."""
        try:
            data = await self.get(key)
            if not data:
                return None

            json_data = json.loads(data)
            return model_class.model_validate(json_data)
        except Exception as e:
            logger.error(f"Error getting model for key {key} from Redis: {e}")
            return None

    async def set_model(
        self, key: str, model: BaseModel, ttl: int | None = None
    ) -> bool:
        """Set a Pydantic model in Redis with TTL."""
        try:
            json_data = model.model_dump()
            serialized = json.dumps(json_data, cls=UUIDEncoder)
            return await self.set(key, serialized, ttl)
        except Exception as e:
            logger.error(f"Error setting model for key {key} in Redis: {e}")
            return False

    async def get_list(self, key: str, model_class: type[T]) -> list[T]:
        """Get a list of Pydantic models from Redis by key."""
        try:
            data = await self.get(key)
            if not data:
                return []

            json_data = json.loads(data)
            return [model_class.model_validate(item) for item in json_data]
        except Exception as e:
            logger.error(f"Error getting list for key {key} from Redis: {e}")
            return []

    async def set_list(
        self, key: str, models: list[BaseModel], ttl: int | None = None
    ) -> bool:
        """Set a list of Pydantic models in Redis with TTL."""
        try:
            json_data = [model.model_dump() for model in models]
            serialized = json.dumps(json_data, cls=UUIDEncoder)
            return await self.set(
                key, serialized, ttl if ttl is not None else self.default_ttl
            )
        except Exception as e:
            logger.error(f"Error setting list for key {key} in Redis: {e}")
            return False
