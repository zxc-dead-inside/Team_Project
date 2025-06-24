import json
from datetime import timedelta

from core.config import settings
from models.person import Person
from services.cache.base import AbstractCacheStorage
from services.cache_services.base import AbstractPersonCacheService


class PersonCacheService(AbstractPersonCacheService):
    def __init__(self, cache: AbstractCacheStorage):
        self.cache = cache

    async def get_person_list_from_cache(
        self, search_query: str
    ) -> list[Person] | None:
        """Trying to get the data from cache."""

        key = f"{settings.person_index}:person_list:{search_query}"
        data = await self.cache.get(key)
        if not data:
            return None
        return [Person.model_validate_json(item) for item in json.loads(data)]

    async def put_person_list_to_cache(
        self,
        search_query: str,
        data: list[Person],
        ttl: timedelta = settings.default_ttl,
    ):
        """Saves the data to the cache."""

        key = (
            f"{settings.person_index}:"
            f"{data[0].__class__.__name__.lower()}_list:{search_query}"
        )

        items = json.dumps([item.model_dump_json() for item in data])
        await self.cache.set(key, items, ttl)

    async def get_person_from_cache(self, person_id: str) -> Person | None:
        """Trying to get the data from the cache."""

        key = f"{settings.movie_index}:person:{person_id}"

        data = await self.cache.get(key)
        if not data:
            return None
        person = Person.model_validate_json(data)
        return person

    async def put_person_to_cache(
        self, person: Person, ttl: timedelta = settings.default_ttl
    ):
        """Saves the data to the cache."""

        key = f"{settings.movie_index}:{person.cache_key}"
        await self.cache.set(key, person.model_dump_json(), ttl)
