import random
from functools import lru_cache
from uuid import UUID

from core.config import settings
from db.elastic import get_elastic
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models.movies_models import (
    MovieDetailResponse, MovieShortListResponse,
    serialize_movie_short_list)
from redis.asyncio import Redis
from services.utils import UUIDEncoder
from services.search_platform.film_es import FilmSearchService
from services.search_platform.di import get_film_sp_service
from services.cache.di import get_film_cache_service
from services.cache.film_cache import FilmCacheService


class FilmService:
    """The main logic of working with films."""

    def __init__(self, cache_service: FilmCacheService, elastic: FilmSearchService):
        self.cache_service = cache_service
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> MovieDetailResponse | None:
        """Returns detail film's info by id."""

        film = await self.cache_service.get_film_from_cache(film_id)
        if not film:
            # Поиск фильма в Elasticsearch
            film = await self.elastic.get_film_from_sp(film_id)
            if not film:
                return None
            await self.cache_service.put_film_to_cache(film, ttl=film.cache_ttl)
        return film

    async def search_by_query(
            self, page_number: int, page_size: int, search_query: str = None
            ) -> list[MovieShortListResponse] | None:
        """Returns the lif of movies by query."""

        films = await self.cache_service.get_films_from_cache(search_query)
        if not films:
            films = await self.elastic.search_film_in_sp(
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
            films = await self.elastic.search_film_general_in_sp(
                page_number, page_size, sort,genre)
            if not films:
                # Если он отсутствует в Elasticsearch, значит,
                # фильма вообще нет в базе.
                return None
            await self.cache_service.put_films_to_cache(key, films)
        return films

    async def get_similar_by_id(
            self, film_id: str, page_number: int, page_size: int
            ) -> list[MovieShortListResponse] | None:
        """Trying to get similar movies by film'd id."""

        film = await self.elastic.get_film_from_sp(film_id)
        if not film:
            return None

        genre_id = random.choice(film.genres).id
        sort = '-imdb_rating'
        key = f"{page_number}:{page_size}:{sort}:{genre_id}"
        
        similar_films = await self.cache_service.get_films_from_cache(key)
        if not similar_films:
            # Ищим фильм в Elasticsearch
            similar_films = await self.elastic.search_film_general_in_sp(
                page_number=page_number,
                page_size=page_size,
                sort=sort,
                genre=genre_id
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
            films = await self.elastic.search_film_general_in_sp(
                page_number=page_number,
                page_size=page_size,
                sort=sort,
                genre=genre_id
            )
            if not films:
                return None
            await self.cache_service.put_films_to_cache(key, films)
        return films


@lru_cache()
def get_film_service(
        cache_service: FilmCacheService = Depends(get_film_cache_service),
        elastic: FilmSearchService = Depends(get_film_sp_service)
) -> FilmService:
    return FilmService(cache_service, elastic)