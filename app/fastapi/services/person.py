import json
from datetime import timedelta
from functools import lru_cache
from typing import Optional, List

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from core.config import settings
from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person, PersonF
# from models.models import PersonBase
from services.utils import UUIDEncoder


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_list(
            self, page_number: int, page_size: int,
            sort: str = None) -> List[Optional[Person]]:
        
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
            sort: str = None) -> List[Optional[Person]]:
        try:
            skip = (page_number - 1) * page_size
            body = {
                "from": skip,
                "size": page_size,
                "_source": ["id", "full_name"]
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

    async def _get_list_from_cache(self, key: str) -> List[Optional[Person]]:
        """Trying to get the data from cache."""

        data = await self.redis.get(
            f"{settings.PERSON_INDEX}:{json.dumps(key)}")
        if not data:
             return None
        return [Person(**dict(item)) for item in json.loads(data)]
    
    async def _put_list_to_cache(
            self, key: str, data: List[Person],
            ttl: timedelta = settings.DEFAULT_TTL):
        
        items = json.dumps([item.__dict__ for item in data], cls=UUIDEncoder)
        await self.redis.set(
            f"{settings.PERSON_INDEX}:{json.dumps(key)}",
            items, ttl)

    async def search_query(
            self,
            page_number: int,
            page_size: int,
            search_query: str = None
            ) -> List[Optional[PersonF]]:
        persons = await self._search_query(
            page_number,
            page_size,
            search_query
        )
        if not persons:
            return None
        return persons

    async def _search_query(
        self,
        page_number: int,
        page_size: int,
        search_query: str = None
            ) -> List[Optional[PersonF]]:
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
            PersonF(**person['_source']) for person in doc['hits']['hits']
        ]

    async def get_by_id(self, person_id: str) -> Optional[PersonF]:
        person = await self._get_person_from_elastic(person_id)
        if not person:
            return None
        return person

    async def _get_person_from_elastic(
            self,
            person_id: str
            ) -> Optional[PersonF]:
        try:
            doc = await self.elastic.get(
                index=settings.PERSON_INDEX,
                id=person_id
            )
        except NotFoundError:
            return None
        return PersonF(**doc['_source'])

    """async def get_films_by_person_id(
            self,
            person_id: str
            ) -> Optional[Person]:
        person = await self._get_person_from_elastic(person_id)
        if not person:
            return None
        film_service = get_film_service()

        films = [
            await film_service.get_by_id(filmrole.id)
            for filmrole in person.films
        ]
        return films"""


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic)
) -> PersonService:
    return PersonService(redis, elastic)
