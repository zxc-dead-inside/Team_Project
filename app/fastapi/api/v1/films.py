from http import HTTPStatus
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.elasticsearch import es_client
from models.models import (
    MovieSearchResponse,
    MovieShort,
    MovieFull,
    serialize_film_detail
)
from services.film import FilmService, get_film_service


router = APIRouter()


# Модель ответа API
class Person(BaseModel):
    uuid: UUID
    full_name: str


class Genre(BaseModel):
    name: str


class FilmDetailed(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float
    description: str
    genre: List[str]
    actors: List[Person]
    directors: List[Person]
    writers: List[Person]


class FilmSearch(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float


class FilmGeneral(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float


@router.get('/', response_model=List[FilmGeneral])
async def film_general(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: str | None = None,
    genre: UUID | None = None,
    film_service: FilmService = Depends(get_film_service)
) -> List[FilmGeneral]:
    films = await film_service.search_general(
        page_number=page_number,
        page_size=page_size,
        sort=sort,
        genre=genre
    )
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Films not found'
        )
    return [
        FilmGeneral(
            uuid=film.id,
            title=film.title,
            imdb_rating=film.imdb_rating
        ) for film in films
    ]


@router.get('/search', response_model=List[FilmSearch])
async def film_search(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search_query: str | None = Query(None, alias="query"),
    film_service: FilmService = Depends(get_film_service)
) -> List[FilmSearch]:
    films = await film_service.search_by_query(
        page_number=page_number,
        page_size=page_size,
        search_query=search_query,
    )
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Films not found'
        )
    return [
        FilmSearch(
            uuid=film.id,
            title=film.title,
            imdb_rating=film.imdb_rating
        ) for film in films
    ]


# Внедряем FilmService с помощью Depends(get_film_service)
@router.get('/{film_id}', response_model=FilmDetailed)
async def film_details(
    film_id: str,
    film_service: FilmService = Depends(get_film_service)
) -> FilmDetailed:
    film = await film_service.get_by_id(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус.
        # Желательно пользоваться уже определёнными HTTP-статусами,
        # которые cодержат enum. Такой код будет более поддерживаемым.
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Film not found'
        )
    # Перекладываем данные из models.Film в Film.
    # Обратите внимание, что у модели бизнес-логики есть поле description,
    # которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и
    # формирования ответов API, вы бы предоставляли клиентам данные,
    # которые им не нужны, и, возможно, данные, которые опасно возвращать
    tmp = FilmDetailed(
        uuid=film.id,
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        genre=film.genres,
        actors=[
            Person(uuid=actor.id, full_name=actor.name)
            for actor in film.actors
        ],
        directors=[
            Person(uuid=actor.id, full_name=actor.name)
            for actor in film.directors
        ],
        writers=[
            Person(uuid=actor.id, full_name=actor.name)
            for actor in film.writers
        ],
    )
    return FilmDetailed(
        uuid=film.id,
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        genre=film.genres,
        actors=[
            Person(uuid=actor.id, full_name=actor.name)
            for actor in film.actors
        ],
        directors=[
            Person(uuid=actor.id, full_name=actor.name)
            for actor in film.directors
        ],
        writers=[
            Person(uuid=actor.id, full_name=actor.name)
            for actor in film.writers
        ],
    )
