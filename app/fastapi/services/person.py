from functools import lru_cache

from fastapi import Depends
from models.person import Person
from services.cache.di import get_person_cache_service
from services.cache.person_cache import PersonCacheService
from services.search_platform.di import get_person_sp_service
from services.search_platform.person_sp import PersonSearchService


class PersonService:
    def __init__(
            self, cache_service: PersonCacheService,
            search_platform: PersonSearchService):

        self.cache_service = cache_service
        self.search_platform = search_platform

    async def get_list(
            self, page_number: int, page_size: int,
            sort: str = None) -> list[Person] | None:
        """Getting list of people."""

        search_query  = f"{page_number}:{page_size}:{sort}"
        persons = await self.cache_service.get_person_list_from_cache(search_query)
        if not persons:
            persons = await self.search_platform.get_persons_from_sp(
                page_number=page_number, page_size=page_size, sort=sort)
            if not persons:
                return None
            await self.cache_service.put_person_list_to_cache(search_query, persons)
        return persons

    async def search_query(
            self, page_number: int, page_size: int,
            search_query: str = None) -> list[Person] | None:
        """Search people in search platform."""
        
        key  = f"{page_number}:{page_size}:{search_query}"
        persons = await self.cache_service.get_person_list_from_cache(key)
        if not persons:
            persons = await self.search_platform.search_person_in_sp(
                page_number, page_size, search_query)
            if not persons:
                return None
            await self.cache_service.put_person_list_to_cache(key, persons)
        return persons

    async def get_by_id(self, person_id: str) -> Person | None:
        """Return detail person by person_id."""
        
        person = await self.cache_service.get_person_from_cache(person_id)
        if not person:
            person = await self.search_platform.get_person_from_sp(person_id)
            
            if not person:
                return None
            await self.cache_service.put_person_to_cache(person)
        return person


@lru_cache()
def get_person_service(
        cache_service: PersonCacheService = Depends(get_person_cache_service),
        elastic: PersonSearchService = Depends(get_person_sp_service)
) -> PersonService:
    return PersonService(cache_service, elastic)
