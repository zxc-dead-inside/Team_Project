from functools import lru_cache
from typing import Optional, List

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from core.config import settings
from db.elastic import get_elastic
from models.person import Person


class PersonService:
    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_list(
            self,
            page_number: int,
            page_size: int,
            sort: str = None
            ) -> List[Optional[Person]]:
    
        persons = await self._get_list(
            page_number=page_number,
            page_size=page_size,
            sort=sort
        )
        if not persons:
            return None
        return persons

    async def _get_list(
            self,
            page_number: int,
            page_size: int,
            sort: str = None
            ) -> List[Optional[Person]]:
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

    async def search_query(
            self,
            page_number: int,
            page_size: int,
            search_query: str = None
            ) -> List[Optional[Person]]:
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
            ) -> List[Optional[Person]]:
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

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._get_person_from_elastic(person_id)
        if not person:
            return None
        return person

    async def _get_person_from_elastic(
            self,
            person_id: str
            ) -> Optional[Person]:
        try:
            doc = await self.elastic.get(
                index=settings.PERSON_INDEX,
                id=person_id
            )
        except NotFoundError:
            return None
        return Person(**doc['_source'])

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
        elastic: AsyncElasticsearch = Depends(get_elastic)
) -> PersonService:
    return PersonService(elastic)
