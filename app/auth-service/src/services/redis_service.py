"""Redis service for caching and session management."""

import redis.asyncio as redis


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
    """Service for Redis operations."""

    def __init__(self, redis_url: str):
        """Initialize the Redis service with the given URL."""
        self.redis_url = redis_url
        self.client = redis.from_url(redis_url)

    async def set(self, key: str, value: str, expire: int = None) -> bool:
        """
        Set a key-value pair in Redis.

        Args:
            key: Key to set
            value: Value to set
            expire: Expiration time in seconds (optional)

        Returns:
            bool: True if the operation was successful
        """
        return await self.client.set(key, value, ex=expire)

    async def get(self, key: str) -> str:
        """
        Get a value from Redis.

        Args:
            key: Key to get

        Returns:
            str: Value for the key or None if not found
        """
        return await self.client.get(key)

    async def delete(self, key: str) -> int:
        """
        Delete a key from Redis.

        Args:
            key: Key to delete

        Returns:
            int: Number of keys deleted
        """
        return await self.client.delete(key)

    async def close(self) -> None:
        """Close the Redis connection."""
        await self.client.close()