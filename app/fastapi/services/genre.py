from functools import lru_cache

from fastapi import Depends
from models.genre import Genre
from services.cache.di import get_genre_cache_service
from services.cache.genre_cache import GenreCacheService
from services.search_platform.di import get_genre_search_platform_service
from services.search_platform.genre_search_platform import GenreSearchSerivce


class GenreService:
    def __init__(
            self, cache_service: GenreCacheService,
            search_platform: GenreSearchSerivce):
        self.cache_service = cache_service
        self.search_platform = search_platform

    async def get_list(
            self, page_number: int, page_size: int,
            sort: str = None) -> list[Genre] | None:
        
        search_query  = f"{page_number}:{page_size}:{sort}"
        genres = (
            await self.cache_service.get_genre_list_from_cache(search_query)
        )
        if not genres:
            genres = await self.search_platform.get_genres(
                page_number=page_number, page_size=page_size, sort=sort)
            if not genres:
                return None
            await (
                self.cache_service
                .put_genre_list_to_cache(search_query, genres)
            )
        return genres

    async def get_by_id(self, genre_id: str) -> Genre | None:

        genre = await self.cache_service.get_genre_from_cache(genre_id)
        if not genre:
            genre = await self.search_platform.get_genre(genre_id)
            if not genre:
                return None
        await self.cache_service.put_genre_to_cache(genre)
        return genre


@lru_cache()
def get_genre_service(
    cache_service: GenreCacheService = Depends(get_genre_cache_service),
    elastic: GenreSearchSerivce = Depends(get_genre_search_platform_service)
) -> GenreService:
    return GenreService(cache_service, elastic)
