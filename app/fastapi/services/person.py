from models.person import Person
from services.base import AbstractService
from services.cache_services.base import AbstractPersonCacheService
from services.search_services.base import AbstractPersonSearchService


class PersonService(AbstractService):
    """The main logic of working with persons."""

    def __init__(
            self, cache_service: AbstractPersonCacheService,
            search_platform: AbstractPersonSearchService):

        self.cache_service = cache_service
        self.search_platform = search_platform

    async def search_query(
            self, page_number: int, page_size: int,
            search_query: str | None = None,
            sort: str | None = None ) -> list[Person] | None:
        """Search persons in search platform."""
        
        key  = f"{page_number}:{page_size}:{sort}:{search_query}"
        persons = await self.cache_service.get_person_list_from_cache(key)
        if not persons:
            persons = (
                await self.search_platform.search_person_in_search_platform(
                    page_number, page_size, search_query
                )
            )
            if not persons:
                return None
            await self.cache_service.put_person_list_to_cache(key, persons)
        return persons

    async def get_by_id(self, person_id: str) -> Person | None:
        """Return detail person by person_id."""
        
        person = await self.cache_service.get_person_from_cache(person_id)
        if not person:
            person = (
                await self.search_platform
                .get_person_from_search_platform(person_id)
            )
            
            if not person:
                return None
            await self.cache_service.put_person_to_cache(person)
        return person
