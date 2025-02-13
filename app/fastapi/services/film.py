import random
from functools import lru_cache
from uuid import UUID

from fastapi import Depends

from models.movies_models import (
    MovieDetailResponse, MovieShortListResponse)
from services.base import AbstractService
from services.cache.film_cache import FilmCacheService
from services.search_platform.film_search_platform import FilmSearchService


class FilmService(AbstractService):
    """The main logic of working with films."""

    def __init__(
            self, cache_service: FilmCacheService,
            search_platform: FilmSearchService):

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
            self, page_number: int, page_size: int, search_query: str = None
            ) -> list[MovieShortListResponse] | None:
        """Returns the list of movies by query."""

        films = await self.cache_service.get_films_from_cache(search_query)
        if not films:
            films = await self.search_platform.search_film_in_search_platform(
                page_number,
                page_size,
                search_query
            )
            if not films:
                return None
    
            await self.cache_service.put_films_to_cache(search_query, films)
        return films

    async def search_general(
            self, page_number: int, page_size: int, sort: str = None,
            genre: UUID = None) -> list[MovieShortListResponse] | None:
        """Trying to get the date for main page."""

        key = f"{page_number}:{page_size}{sort}:{genre}"
        films = await self.cache_service.get_films_from_cache(key)
        if not films:
            films = (
                await self.search_platform
                .search_film_general_in_search_platform(
                    page_number, page_size, sort,genre
                )
            )
            if not films:
                # Если он отсутствует в search platform, значит,
                # фильма вообще нет в базе.
                return None
            await self.cache_service.put_films_to_cache(key, films)
        return films

    async def get_similar_by_id(
            self, film_id: str, page_number: int, page_size: int
            ) -> list[MovieShortListResponse] | None:
        """Trying to get similar movies by film'd id."""

        film = (
            await self.search_platform.get_film_from_search_platform(film_id)
        )
        if not film:
            return None

        genre_id = random.choice(film.genres).id
        sort = '-imdb_rating'
        key = f"{page_number}:{page_size}:{sort}:{genre_id}"
        
        similar_films = await self.cache_service.get_films_from_cache(key)
        if not similar_films:
            # Searching movie on search platform
            similar_films = (
                await self.search_platform
                .search_film_general_in_search_platform(
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
                await self.search_platform
                .search_film_general_in_search_platform(
                    page_number=page_number, page_size=page_size,
                    sort=sort, genre=genre_id
                )
            )           
            if not films:
                return None
            await self.cache_service.put_films_to_cache(key, films)
        return films
