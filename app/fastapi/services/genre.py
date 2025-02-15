from models.genre import Genre
from services.base import AbstractService
from services.cache_services.base import AbstractGenreCacheService
from services.search_services.base import AbstractGenreSearchService


class GenreService(AbstractService):

    """The main logic of working with genres."""
    def __init__(
            self, cache_service: AbstractGenreCacheService,
            search_platform: AbstractGenreSearchService):
        self.cache_service = cache_service
        self.search_platform = search_platform

    async def search_query(
            self, page_number: int, page_size: int,
            sort: str = None) -> list[Genre] | None:
        """Getting list of genres."""

        search_query  = f"{page_number}:{page_size}:{sort}"
        genres = (
            await self.cache_service.get_genre_list_from_cache(search_query)
        )
        if not genres:
            genres = await self.search_platform.get_genres_in_search_platform(
                page_number=page_number, page_size=page_size, sort=sort)
            if not genres:
                return None
            await (
                self.cache_service
                .put_genre_list_to_cache(search_query, genres)
            )
        return genres

    async def get_by_id(self, genre_id: str) -> Genre | None:
        """Return genre name by id."""
        
        genre = await self.cache_service.get_genre_from_cache(genre_id)
        if not genre:
            genre = await self.search_platform.get_genre_from_search_platform(
                genre_id)
            if not genre:
                return None
        await self.cache_service.put_genre_to_cache(genre)
        return genre
