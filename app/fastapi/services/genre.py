from functools import lru_cache
from typing import Optional, List

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from models.genre import Genre
from core.config import settings


class GenreService:
    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_list(
            self,
            page_number: int,
            page_size: int,
            sort: str = None
            ) -> List[Optional[Genre]]:
        genres = await self._get_list(
            page_number=page_number,
            page_size=page_size,
            sort=sort
        )
        if not genres:
            return None
        return genres

    async def _get_list(
            self,
            page_number: int,
            page_size: int,
            sort: str = None
            ) -> List[Optional[Genre]]:
        try:
            skip = (page_number - 1) * page_size
            body = {
                "from": skip,
                "size": page_size,
                "_source": ["id", "name"],
            }
            if sort:
                body["sort"] = [{
                    sort.lstrip("-"): {
                        "order": "desc" if sort.startswith("-") else "asc"
                    }
                }]
            doc = await self.elastic.search(
                index=settings.GENRE_INDEX,
                body=body
            )
        except NotFoundError:
            return None
        return [Genre(**genre['_source']) for genre in doc['hits']['hits']]

    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        genre = await self._get_genre_from_elastic(genre_id)
        if not genre:
            return None
        return genre

    async def _get_genre_from_elastic(
            self,
            genre_id: str
            ) -> Optional[Genre]:
        try:
            doc = await self.elastic.get(
                index=settings.GENRE_INDEX,
                id=genre_id
            )
        except NotFoundError:
            return None
        return Genre(**doc['_source'])


@lru_cache()
def get_genre_service(
        elastic: AsyncElasticsearch = Depends(get_elastic)
) -> GenreService:
    return GenreService(elastic)
