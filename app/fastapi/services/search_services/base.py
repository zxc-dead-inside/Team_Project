from abc import ABC, abstractmethod

from services.search_platform.base import AbstractSearchPlatfrom


class AbstractSearchService(ABC):
    """Abstract class for search service."""

    def __init__(self, search_platform: AbstractSearchPlatfrom):
        self.search_platform = search_platform


class AbstractFilmSearchService(AbstractSearchService):
    """Abstract class for Film search service."""

    @abstractmethod
    async def get_film_from_search_platform(self):
        pass

    @abstractmethod
    async def search_film_in_search_platform(self):
        pass


class AbstractGenreSearchService(AbstractSearchService):
    """Abstract class for Genre search service."""

    @abstractmethod
    async def get_genre_from_search_platform(self):
        pass

    @abstractmethod
    async def get_genres_in_search_platform(self):
        pass


class AbstractPersonSearchService(AbstractSearchService):
    """Abstract class for Person search service."""

    @abstractmethod
    async def get_person_from_search_platform(self):
        pass

    @abstractmethod
    async def search_person_in_search_platform(self):
        pass
