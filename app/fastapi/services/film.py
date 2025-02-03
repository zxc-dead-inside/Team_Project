from functools import lru_cache
from typing import Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from typing import List

from db.elastic import get_elastic
from models.film import Film, FilmSearch, FilmGeneral
from core.config import settings


# FilmService содержит бизнес-логику по работе с фильмами.
# Никакой магии тут нет. Обычный класс с обычными методами.
# Этот класс ничего не знает про DI — максимально сильный и независимый.
class FilmService:
    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    # get_by_id возвращает объект фильма.
    # Он опционален, так как фильм может отсутствовать в базе.
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        # Ищим фильм в Elasticsearch
        film = await self._get_film_from_elastic(film_id)
        if not film:
            # Если он отсутствует в Elasticsearch, значит,
            # фильма вообще нет в базе.
            return None
        return film

    async def search_by_query(
            self,
            page_number: int,
            page_size: int,
            search_query: str = None
            ) -> List[Optional[FilmSearch]]:
        films = await self._search_film_in_elastic(
            page_number,
            page_size,
            search_query
        )
        if not films:
            # Если он отсутствует в Elasticsearch, значит,
            # фильма вообще нет в базе.
            return None
        return films

    async def search_general(
            self,
            page_number: int,
            page_size: int,
            sort: str = None,
            genre: UUID = None
            ) -> List[Optional[FilmGeneral]]:
        films = await self._search_general_filmsin_elastic(
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

    async def _get_film_from_elastic(
            self,
            film_id: str
            ) -> Optional[FilmSearch]:
        try:
            doc = await self.elastic.get(
                index=settings.MOVIE_INDEX,
                id=film_id
            )
        except NotFoundError:
            return None
        return Film(**doc['_source'])

    async def _search_films_in_elastic(
            self,
            page_number: int,
            page_size: int,
            search_query: str = None
            ) -> List[Optional[FilmSearch]]:
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
                                "title^3",
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
        return [FilmSearch(**film['_source']) for film in doc['hits']['hits']]

    async def _search_general_filmsin_elastic(
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

            # TODO: Изменить ETL, чтобы в индекс фильмов загружались
            # идентификаторы жанров.
            """if genre:
                response = await es_client.get(
                    index=settings.GENRE_INDEX
                    id=genre
                )
                genre_name = response['_source']['name']
                query["bool"]["filter"] = [
                    {"term": {"genres": str(genre_name)}}
                ]"""
            doc = await self.elastic.search(
                index=settings.MOVIE_INDEX,
                body=body
            )
        except NotFoundError:
            return None
        return [FilmGeneral(**film['_source']) for film in doc['hits']['hits']]


# get_film_service — это провайдер FilmService.
# С помощью Depends он сообщает, что ему необходимы Redis и Elasticsearch
# Для их получения вы ранее создали функции-провайдеры в модуле db
# Используем lru_cache-декоратор, чтобы создать объект сервиса в
# едином экземпляре (синглтона)
@lru_cache()
def get_film_service(
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(elastic)
