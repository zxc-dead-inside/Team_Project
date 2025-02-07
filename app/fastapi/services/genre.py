import json
from datetime import timedelta
from functools import lru_cache
from typing import Optional, List

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre
from core.config import settings
from services.utils import UUIDEncoder


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_list(
            self, page_number: int, page_size: int,
            sort: str = None) -> List[Optional[Genre]]:
        
        key  = f"{page_number}:{page_size}:{sort}"
        genres = await self._get_list_from_cache(key)
        if not genres:
            genres = await self._get_list(
                page_number=page_number, page_size=page_size, sort=sort)
            if not genres:
                return None
            await self._put_list_to_cache(key, genres)
        return genres
    
    async def _get_list_from_cache(self, key: str) -> List[Optional[Genre]]:
        """Trying to get the data from cache."""

        data = await self.redis.get(
            f"{settings.GENRE_INDEX}:{json.dumps(key)}")
        if not data:
             return None
        return [Genre(**dict(item)) for item in json.loads(data)]
    
    async def _put_list_to_cache(
            self, key: str, data: List[Genre],
            ttl: timedelta = settings.DEFAULT_TTL):

        items = json.dumps([item.__dict__ for item in data], cls=UUIDEncoder)
        await self.redis.set(
            f"{settings.GENRE_INDEX}:{json.dumps(key)}",
            items, ttl)

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

        genre = await self._get_genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
        await self._put_genre_to_cache(genre)
        return genre
    
    async def _get_genre_from_cache(self, genre_id: str) -> Optional[Genre]:
        """Trying to get the genre by id."""

        genre = await self.redis.get(f"{settings.GENRE_INDEX}:{genre_id}")
        if not genre:
            return None

        return Genre.model_validate_json(genre)
    
    async def _put_genre_to_cache(
            self, genre: Genre, ttl: timedelta = settings.DEFAULT_TTL):
        """Saves the genre to the cache."""

        await self.redis.set(
            f"{settings.GENRE_INDEX}:{str(genre.id)}",
            genre.model_dump_json(), ttl)

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
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic)
) -> GenreService:
    return GenreService(redis, elastic)
