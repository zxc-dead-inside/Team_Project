from abc import ABC, abstractmethod


class AbstractCacheStorage(ABC):
    """Abstract class for cache storage."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> None:
        pass
