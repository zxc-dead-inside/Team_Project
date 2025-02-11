from  typing import Any

from elasticsearch import AsyncElasticsearch, NotFoundError

from models.movies_models import MovieDetailResponse, MovieShortListResponse
from services.search_platform.base import AbstractSearchPlatfrom


class EsSearchPlatform(AbstractSearchPlatfrom):
    """Class for using elasticsearch."""

    def __init__(self, es: AsyncElasticsearch):
        self.es = es

    async def get(
        self, index: str, obj_id: str) -> dict[str, Any] | None:
        try:
            result = await self.es.get(index=index, id=obj_id)
        except NotFoundError:
            return None
        return result

    async def search(
        self, index: str, body: dict[str, Any]
        ) -> dict[str, Any] | None:
        try:
            results = await self.es.search(index=index, body=body)
        except NotFoundError:
            return None
        return results