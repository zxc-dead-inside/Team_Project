import json
from datetime import timedelta
from functools import lru_cache

from core.config import settings
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models.genre import Genre
from redis.asyncio import Redis
from services.utils import UUIDEncoder


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_list(
            self, page_number: int, page_size: int,
            sort: str = None) -> list[Genre] | None:
        
        search_query  = f"{page_number}:{page_size}:{sort}"
        genres = await self._get_list_from_cache(search_query)
        if not genres:
            genres = await self._get_list(
                page_number=page_number, page_size=page_size, sort=sort)
            if not genres:
                return None
            await self._put_list_to_cache(search_query, genres)
        return genres
    
    async def _get_list_from_cache(
            self, search_query: str) -> list[Genre] | None:
        """Trying to get the data from cache."""

        key = (
            f"{settings.genre_index}:"
            f"genre_list:{search_query}")

        data = await self.redis.get(key)
        if not data:
             return None
        return [Genre(**dict(item)) for item in json.loads(data)]
    
    async def _put_list_to_cache(
            self, search_query: str, data: list[Genre],
            ttl: timedelta = settings.default_ttl):
        
        key = (
            f"{settings.genre_index}:"
            f"{data[0].__class__.__name__.lower()}_list:{search_query}")

        items = json.dumps([item.__dict__ for item in data], cls=UUIDEncoder)
        await self.redis.set(key, items, ttl)

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

        genre = await self._get_genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
        await self._put_genre_to_cache(genre)
        return genre
    
    async def _get_genre_from_cache(self, genre_id: str) -> Genre | None:
        """Trying to get the genre by id."""

        key = (f"{settings.genre_index}:genre:{genre_id}")
        genre = await self.redis.get(key)
        if not genre:
            return None

        return Genre.model_validate_json(genre)
    
    async def _put_genre_to_cache(
            self, genre: Genre, ttl: timedelta = settings.default_ttl):
        """Saves the genre to the cache."""

        key = (f"{settings.genre_index}:{genre.cache_key}")

        await self.redis.set(key, genre.model_dump_json(), ttl)

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
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic)
) -> GenreService:
    return GenreService(redis, elastic)
