from abc import ABC, abstractmethod

from services.cache.base import AbstractCacheStorage


class AbstractCacheService(ABC):
    """Abstract class for cache service."""
    def __init__(
            self, cache: AbstractCacheStorage
    ):
        self.cache = cache


class AbstractPersonCacheService(AbstractCacheService):
    """Abstract class for Person cache service."""

    @abstractmethod
    async def get_person_list_from_cache(self):
        pass

    @abstractmethod
    async def put_person_list_to_cache(self):
        pass

    @abstractmethod
    async def get_person_from_cache(self):
        pass

    @abstractmethod
    async def put_person_to_cache(self):
        pass


class AbstractFilmCacheService(AbstractCacheService):
    """Abstract class for Film cache service."""

    @abstractmethod
    async def get_film_from_cache(self):
        pass

    @abstractmethod
    async def put_film_to_cache(self):
        pass

    @abstractmethod
    async def get_films_from_cache(self):
        pass

    @abstractmethod
    async def put_films_to_cache(self):
        pass


class AbstractGenreCacheService(AbstractCacheService):
    """Abstract class for Genre cache service."""

    @abstractmethod
    async def get_genre_from_cache(self):
        pass

    @abstractmethod
    async def put_genre_to_cache(self):
        pass

    @abstractmethod
    async def get_genre_list_from_cache(self):
        pass

    @abstractmethod
    async def put_genre_list_to_cache(self):
        pass
