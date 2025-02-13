from abc import ABC, abstractmethod

from services.cache.base import AbstractCacheStorage
from services.search_platform.base import AbstractSearchPlatfrom


class AbstractService(ABC):
    """Abstract class for search platform."""

    def __init__(
        self, cache_service: AbstractCacheStorage,
        search_platform: AbstractSearchPlatfrom
    ):
        self.cache_service = cache_service
        self.search_platform = search_platform

    @abstractmethod
    async def get_by_id(
        self,
        id: str
    ):
        pass

    @abstractmethod
    async def get_list():
        pass

    @abstractmethod
    async def search_query():
        pass
