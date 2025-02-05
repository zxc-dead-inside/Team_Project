import json
import random

from functools import lru_cache
from typing import List, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film, FilmGeneral
from core.config import settings


# FilmService содержит бизнес-логику по работе с фильмами.
# Никакой магии тут нет. Обычный класс с обычными методами.
# Этот класс ничего не знает про DI — максимально сильный и независимый.
class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    # get_by_id возвращает объект фильма.
    # Он опционален, так как фильм может отсутствовать в базе.
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        # Поиск фильма в кэше
        film = await self._get_film_from_cache(film_id)
        if not film:
            # Поиск фильма в Elasticsearch
            film = await self._get_film_from_elastic(film_id)
            if not film:
            # Если он отсутствует в Elasticsearch, значит,
            # фильма вообще нет в базе.
                return None
            await self._put_film_to_cache(film)
        return film
    
    async def _get_film_from_cache(self, film_id: str) -> Optional[Film]:
        data = await self.redis.get(film_id)
        if not data:
            return None
        film = Film.model_validate_json((data))
        return film
    
    async def _put_film_to_cache(self, film: Film):
        await self.redis.set(
            film.id, film.model_dump_json(), 3600)
        
    async def _get_films_from_cache(
            self, key: str) -> List[Optional[FilmGeneral]]:
        
        data = await self.redis.get(
            f"{settings.MOVIE_INDEX}:{json.dumps(key)}")
        if not data:
            return None
        films = [FilmGeneral(**dict(item)) for item in json.loads(data)]
        return films
    
    async def _put_films_to_cache(self, key: str, data: List[FilmGeneral]):
        films = json.dumps([item.__dict__ for item in data])
        await self.redis.set(
            f"{settings.MOVIE_INDEX}:{json.dumps(key)}",
            films, 3600)

    async def _get_film_from_elastic(
            self,
            film_id: str
            ) -> Optional[Film]:
        try:
            doc = await self.elastic.get(
                index=settings.MOVIE_INDEX,
                id=film_id
            )
        except NotFoundError:
            return None
        return Film(**doc['_source'])

    async def search_by_query(
            self,
            page_number: int,
            page_size: int,
            search_query: str = None
            ) -> List[Optional[FilmGeneral]]:
        
        films = await self._get_films_from_cache(search_query)
        if not films:
            films = await self._search_films_in_elastic(
                page_number,
                page_size,
                search_query
            )
            if not films:
            # Если он отсутствует в Elasticsearch, значит,
            # фильма вообще нет в базе.
                return None
    
            await self._put_films_to_cache(search_query, films)
        return films

    async def _search_films_in_elastic(
            self,
            page_number: int,
            page_size: int,
            search_query: str = None
            ) -> List[Optional[FilmGeneral]]:
        try:
            query = {"bool": {"must": [{"match_all": {}}]}}
            skip = (page_number - 1) * page_size
            body = {
                "query": query,
                "from": skip,
                "size": page_size,
                "_source": ["id", "title", "imdb_rating"],
            }
            if search_query:
                query["bool"]["must"] = [
                    {
                        "multi_match": {
                            "query": search_query,
                            "fields": [
                                "title",
                                "description",
                                "actors_names",
                                "directors_names",
                                "writers_names",
                            ],
                            "type": "cross_fields",
                            "operator": "and",
                        }
                    }
                ]
            body["sort"] = [{"imdb_rating": {"order": "desc"}}]

            doc = await self.elastic.search(
                index=settings.MOVIE_INDEX,
                body=body
            )
        except NotFoundError:
            return None
        return [FilmGeneral(**film['_source']) for film in doc['hits']['hits']]

    async def search_general(
            self,
            page_number: int,
            page_size: int,
            sort: str = None,
            genre: UUID = None
            ) -> List[Optional[FilmGeneral]]:
        films = await self._search_general_films_in_elastic(
            page_number,
            page_size,
            sort,
            genre
        )
        if not films:
            # Если он отсутствует в Elasticsearch, значит,
            # фильма вообще нет в базе.
            return None
        return films

    async def _search_general_films_in_elastic(
            self,
            page_number: int,
            page_size: int,
            sort: str = None,
            genre: UUID = None
            ) -> List[Optional[FilmGeneral]]:
        try:
            query = {"bool": {"must": [{"match_all": {}}]}}
            skip = (page_number - 1) * page_size
            body = {
                "query": query,
                "from": skip,
                "size": page_size,
                "_source": ["id", "title", "imdb_rating"],
            }

            if sort:
                body["sort"] = [{
                    sort.lstrip("-"): {
                        "order": "desc" if sort.startswith("-") else "asc"
                    }
                }]
            if genre:
                query["bool"]["filter"] = [{
                    "nested": {
                        "path": "genres",
                        "query": {
                            "term": {
                                "genres.id": genre
                            }
                        }
                    }
                }]
            doc = await self.elastic.search(
                index=settings.MOVIE_INDEX,
                body=body
            )
        except NotFoundError:
            return None
        return [FilmGeneral(**film['_source']) for film in doc['hits']['hits']]

    async def get_similar_by_id(
            self,
            film_id: str,
            page_number: int,
            page_size: int
            ) -> List[Optional[FilmGeneral]]:
        # Ищим фильм в Elasticsearch
        film = await self._get_film_from_elastic(film_id)
        if not film:
            return None
        similar_films = await self._search_general_films_in_elastic(
            page_number=page_number,
            page_size=page_size,
            sort='-imdb_rating',
            genre=random.choice(film.genres).id
        )
        return similar_films

    async def get_popular_by_genre_id(
            self,
            genre_id: str,
            page_number: int,
            page_size: int
            ) -> List[Optional[FilmGeneral]]:
        films = await self._search_general_films_in_elastic(
            page_number=page_number,
            page_size=page_size,
            sort='-imdb_rating',
            genre=genre_id
        )
        if not films:
            return None
        return films


# get_film_service — это провайдер FilmService.
# С помощью Depends он сообщает, что ему необходимы Redis и Elasticsearch
# Для их получения вы ранее создали функции-провайдеры в модуле db
# Используем lru_cache-декоратор, чтобы создать объект сервиса в
# едином экземпляре (синглтона)
@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic)
) -> FilmService:
    return FilmService(redis, elastic)
