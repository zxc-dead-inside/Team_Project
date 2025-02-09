import json
from datetime import timedelta
from functools import lru_cache

from core.config import settings
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models.person import Person
from redis.asyncio import Redis


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_list(
            self, page_number: int, page_size: int,
            sort: str = None) -> list[Person] | None:
        
        key  = f"{page_number}:{page_size}:{sort}"
        persons = await self._get_list_from_cache(key)
        if not persons:
            persons = await self._get_list(
                page_number=page_number, page_size=page_size, sort=sort)
            if not persons:
                return None
            await self._put_list_to_cache(key, persons)
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
                index=settings.PERSON_INDEX,
                body=body
            )
        except NotFoundError:
            return None
        return [Person(**person['_source']) for person in doc['hits']['hits']]

    async def _get_list_from_cache(self, key: str) -> list[Person] | None:
        """Trying to get the data from cache."""

        data = await self.redis.get(
            f"{settings.PERSON_INDEX}:{json.dumps(key)}")
        if not data:
             return None
        return [Person.model_validate_json(item) for item in json.loads(data)]
    
    async def _put_list_to_cache(
            self, key: str, data: list[Person],
            ttl: timedelta = settings.DEFAULT_TTL):
        """Saves the data to the cache."""
        
        items = json.dumps([item.model_dump_json() for item in data])
        await self.redis.set(
            f"{settings.PERSON_INDEX}:{json.dumps(key)}",
            items, ttl)

    async def search_query(
            self, page_number: int, page_size: int,
            search_query: str = None) -> list[Person] | None:
        
        key  = f"{page_number}:{page_size}:{search_query}"
        persons = await self._get_list_from_cache(key)
        if not persons:
            persons = await self._search_query(
                page_number, page_size, search_query)
            if not persons:
                return None
            await self._put_list_to_cache(key, persons)
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
                index=settings.PERSON_INDEX,
                body=body
            )
        except NotFoundError:
            return None
        return [
            Person(**person['_source']) for person in doc['hits']['hits']
        ]

    async def get_by_id(self, person_id: str) -> Person | None:
        
        person = await self._get_person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            
            if not person:
                return None
            await self._put_person_to_cache(person)
        return person

    async def _get_person_from_cache(
            self, person_id: str) -> Person | None:
        """Trying to get the data from the cache."""

        data = await self.redis.get(f"{settings.PERSON_INDEX}:{person_id}")
        if not data:
            return None
        person = Person.model_validate_json(data)
        return person

    async def _put_person_to_cache(
            self, data: Person,
            ttl: timedelta = settings.DEFAULT_TTL):
        """Saves the data to the cache."""

        await self.redis.set(
            f"{settings.PERSON_INDEX}:{str(data.id)}",
            data.model_dump_json(), ttl)

    async def _get_person_from_elastic(
            self,
            person_id: str
            ) -> Person | None:
        try:
            doc = await self.elastic.get(
                index=settings.PERSON_INDEX,
                id=person_id
            )
        except NotFoundError:
            return None
        return Person(**doc['_source'])


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic)
) -> PersonService:
    return PersonService(redis, elastic)
