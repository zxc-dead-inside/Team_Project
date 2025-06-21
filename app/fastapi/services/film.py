import random
from uuid import UUID

from models.movies_models import (
    MovieDetailResponse, MovieShortListResponse)
from services.base import AbstractService
from services.cache_services.base import AbstractFilmCacheService
from services.search_services.base import AbstractFilmSearchService


class FilmService(AbstractService):
    """The main logic of working with films."""

    def __init__(
            self, cache_service: AbstractFilmCacheService,
            search_platform: AbstractFilmSearchService):

        self.cache_service = cache_service
        self.search_platform = search_platform

    async def get_by_id(self, film_id: str) -> MovieDetailResponse | None:
        """Returns detail film's info by id."""

        film = await self.cache_service.get_film_from_cache(film_id)
        if not film:
            # Поиск фильма в search platform
            film = (
                await self.search_platform
                .get_film_from_search_platform(film_id)
            )
            if not film:
                return None
            await (
                self.cache_service.put_film_to_cache(film, ttl=film.cache_ttl)
            )
        return film

    async def search_query(
            self, page_number: int, page_size: int,
            sort: str | None = None, search_query: str | None = None,
            genre: UUID | None = None) -> list[MovieShortListResponse] | None:
        """Returns the list of movies.
        
        Optional:
            1. Can be filtered by Genre
            2. Can process a search string
        """

        key = f"{page_number}:{page_size}:{sort}:{genre}:{search_query}"
        films = await self.cache_service.get_films_from_cache(key)
        if not films:
            films = await self.search_platform.search_film_in_search_platform(
                page_number=page_number, page_size=page_size,
                search_query=search_query, genre=genre, sort=sort
            )
            if not films:
                return None
    
            await self.cache_service.put_films_to_cache(key, films)
        return films

    async def get_similar_by_id(
            self, film_id: str, page_number: int, page_size: int
            ) -> list[MovieShortListResponse] | None:
        """Trying to get similar movies by film'd id."""

        film = await self.cache_service.get_film_from_cache(film_id)
        if not film:
            film = await self.search_platform.get_film_from_search_platform(
                film_id
            )
            if not film:
                return None
            await self.cache_service.put_film_to_cache(film, film.cache_ttl)

        genre_id = random.choice(film.genres).id
        sort = '-imdb_rating'
        key = f"{page_number}:{page_size}:{sort}:{genre_id}"
        
        similar_films = await self.cache_service.get_films_from_cache(key)
        if not similar_films:
            # Searching movie on search platform
            similar_films = (
                await self.search_platform
                .search_film_in_search_platform(
                    page_number=page_number, page_size=page_size,
                    sort=sort, genre=genre_id
                )
            )
            if not similar_films:
                return None

            await self.cache_service.put_films_to_cache(key, similar_films)
        return similar_films

    async def get_popular_by_genre_id(
            self, genre_id: str, page_number: int, page_size: int
            ) -> list[MovieShortListResponse] | None:
        """Returns the most popular movies in a genre."""

        sort = '-imdb_rating'
        key = f"{page_number}:{page_size}:{sort}:{genre_id}"
        
        films = await self.cache_service.get_films_from_cache(key)
        if not films:
            films = (
                await self.search_platform.search_film_in_search_platform(
                    page_number=page_number, page_size=page_size,
                    sort=sort, genre=genre_id
                )
            )           
            if not films:
                return None
            await self.cache_service.put_films_to_cache(key, films)
        return films
