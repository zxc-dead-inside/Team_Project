from functools import lru_cache

from core.config import settings
from db.elastic import get_elastic
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models.genre import Genre
from services.cache.di import get_genre_cache_service
from services.cache.genre_cache import GenreCacheService


class GenreService:
    def __init__(self, cache_service: GenreCacheService, elastic: AsyncElasticsearch):
        self.cache_service = cache_service
        self.elastic = elastic

    async def get_list(
            self, page_number: int, page_size: int,
            sort: str = None) -> list[Genre] | None:
        
        search_query  = f"{page_number}:{page_size}:{sort}"
        genres = await self.cache_service.get_genre_list_from_cache(search_query)
        if not genres:
            genres = await self._get_list(
                page_number=page_number, page_size=page_size, sort=sort)
            if not genres:
                return None
            await self.cache_service.put_genre_list_to_cache(search_query, genres)
        return genres

    async def _get_list(
            self,
            page_number: int,
            page_size: int,
            sort: str = None
            ) -> list[Genre] | None:
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
                index=settings.genre_index,
                body=body
            )
        except NotFoundError:
            return None
        return [Genre(**genre['_source']) for genre in doc['hits']['hits']]

    async def get_by_id(self, genre_id: str) -> Genre | None:

        genre = await self.cache_service.get_genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
        await self.cache_service.put_genre_to_cache(genre)
        return genre

    async def _get_genre_from_elastic(
            self,
            genre_id: str
            ) -> Genre | None:
        try:
            doc = await self.elastic.get(
                index=settings.genre_index,
                id=genre_id
            )
        except NotFoundError:
            return None
        return Genre(**doc['_source'])


@lru_cache()
def get_genre_service(
    cache_service: GenreCacheService = Depends(get_genre_cache_service),
    elastic: AsyncElasticsearch = Depends(get_elastic)
) -> GenreService:
    return GenreService(cache_service, elastic)
