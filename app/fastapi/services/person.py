from functools import lru_cache

from core.config import settings
from db.elastic import get_elastic
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models.person import Person
from services.cache.di import get_person_cache_service
from services.cache.person_cache import PersonCacheService


class PersonService:
    def __init__(self, cache_service: PersonCacheService, elastic: AsyncElasticsearch):
        self.cache_service = cache_service
        self.elastic = elastic

    async def get_list(
            self, page_number: int, page_size: int,
            sort: str = None) -> list[Person] | None:
        
        search_query  = f"{page_number}:{page_size}:{sort}"
        persons = await self.cache_service.get_person_list_from_cache(search_query)
        if not persons:
            persons = await self._get_list(
                page_number=page_number, page_size=page_size, sort=sort)
            if not persons:
                return None
            await self.cache_service.put_person_list_to_cache(search_query, persons)
        return persons

    async def _get_list(
            self, page_number: int, page_size: int,
            sort: str = None) -> list[Person] | None:
        try:
            skip = (page_number - 1) * page_size
            body = {
                "from": skip,
                "size": page_size
            }
            if sort:
                body["sort"] = [{
                    sort.lstrip("-"): {
                        "order": "desc" if sort.startswith("-") else "asc"
                    }
                }]
            doc = await self.elastic.search(
                index=settings.person_index,
                body=body
            )
        except NotFoundError:
            return None
        return [Person(**person['_source']) for person in doc['hits']['hits']]

    async def search_query(
            self, page_number: int, page_size: int,
            search_query: str = None) -> list[Person] | None:
        
        key  = f"{page_number}:{page_size}:{search_query}"
        persons = await self.cache_service.get_person_list_from_cache(key)
        if not persons:
            persons = await self._search_query(
                page_number, page_size, search_query)
            if not persons:
                return None
            await self.cache_service.put_person_list_to_cache(key, persons)
        return persons

    async def _search_query(
        self,
        page_number: int,
        page_size: int,
        search_query: str = None
            ) -> list[Person] | None:
        try:
            query = {"bool": {"must": [{"match_all": {}}]}}
            skip = (page_number - 1) * page_size
            body = {
                "query": query,
                "from": skip,
                "size": page_size,
                "_source": ["id", "full_name", "films"]
            }
            if search_query:
                query["bool"]["must"] = [
                    {
                        "match": {"full_name": search_query}
                    }
                ]
            doc = await self.elastic.search(
                index=settings.person_index,
                body=body
            )
        except NotFoundError:
            return None
        return [
            Person(**person['_source']) for person in doc['hits']['hits']
        ]

    async def get_by_id(self, person_id: str) -> Person | None:
        
        person = await self.cache_service.get_person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            
            if not person:
                return None
            await self.cache_service.put_person_to_cache(person)
        return person

    async def _get_person_from_elastic(
            self,
            person_id: str
            ) -> Person | None:
        try:
            doc = await self.elastic.get(
                index=settings.person_index,
                id=person_id
            )
        except NotFoundError:
            return None
        return Person(**doc['_source'])


@lru_cache()
def get_person_service(
        cache_service: PersonCacheService = Depends(get_person_cache_service),
        elastic: AsyncElasticsearch = Depends(get_elastic)
) -> PersonService:
    return PersonService(cache_service, elastic)
