
from elasticsearch import NotFoundError

from core.config import settings
from models.person import (
    Person, serialize_person_detail, serialize_person_list)
from services.search_platform.base import AbstractSearchPlatfrom


class PersonSearchService:
    """"
    A service class responsible for retrieving person data from search
    platform.
    """

    def __init__(self, search_platform: AbstractSearchPlatfrom):
        self.search_platform = search_platform

    async def get_person_from_search_platform(
            self, person_id: str) -> Person | None:
        """Returns person by id."""

        result =  await self.search_platform.get(settings.person_index, person_id)
        if result is None:
            return None
        return await serialize_person_detail(result)

    async def search_person_in_search_platform(
            self, page_number: int, page_size: int,
            search_query: str | None = None, sort: str | None = None) -> list[Person] | None:
        """Returns list of people."""

        query = {"bool": {"must": [{"match_all": {}}]}}
        skip = (page_number - 1) * page_size
        body = {
            "query": query,
            "from": skip,
            "size": page_size,
            "_source": ["id", "full_name", "films"]
        }
        if sort:
            body["sort"] = [{
                sort.lstrip("-"): {
                    "order": "desc" if sort.startswith("-") else "asc"
                }
            }]
        if search_query:
            query["bool"]["must"] = [
                {
                    "match": {"full_name": search_query}
                }
            ]
        try:
            results = await self.search_platform.search(
                index=settings.person_index,
                body=body
            )
        except NotFoundError:
            return None
        return await serialize_person_list(results)
