import json
from datetime import timedelta

from core.config import settings
from models.genre import Genre
from services.cache.base import AbstractCacheStorage
from services.cache_services.base import AbstractGenreCacheService
from services.utils import UUIDEncoder


class GenreCacheService(AbstractGenreCacheService):
    def __init__(self, cache: AbstractCacheStorage):
        self.cache = cache

    async def get_genre_from_cache(self, genre_id: str) -> Genre | None:
        """Trying to get the genre by id."""

        key = f"{settings.genre_index}:genre:{genre_id}"
        genre = await self.cache.get(key)
        if not genre:
            return None

        return Genre.model_validate_json(genre)

    async def put_genre_to_cache(
        self, genre: Genre, ttl: timedelta = settings.default_ttl
    ):
        """Saves the genre to the cache."""

        key = f"{settings.genre_index}:{genre.cache_key}"

        await self.cache.set(key, genre.model_dump_json(), ttl)

    async def get_genre_list_from_cache(self, search_query: str) -> list[Genre] | None:
        key = f"{settings.genre_index}:genre_list:{search_query}"

        data = await self.cache.get(key)
        if not data:
            return None
        return [Genre(**dict(item)) for item in json.loads(data)]

    async def put_genre_list_to_cache(
        self,
        search_query: str,
        data: list[Genre],
        ttl: timedelta = settings.default_ttl,
    ):
        key = (
            f"{settings.genre_index}:"
            f"{data[0].__class__.__name__.lower()}_list:{search_query}"
        )

        items = json.dumps([item.__dict__ for item in data], cls=UUIDEncoder)
        await self.cache.set(key, items, ttl)
