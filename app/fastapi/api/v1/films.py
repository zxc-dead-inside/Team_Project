from http import HTTPStatus
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from models.models import Genre, MovieFull, MovieShort, Person
from services.film import FilmService, get_film_service


router = APIRouter()


@router.get('/popular', response_model=List[MovieShort])
async def films_popular_by_genre(
    genre: str,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    film_service: FilmService = Depends(get_film_service)
) -> List[MovieShort]:
    popular_films = await film_service.get_popular_by_genre_id(
        genre,
        page_number=page_number,
        page_size=page_size
    )
    if not popular_films:
        # Если фильм не найден, отдаём 404 статус.
        # Желательно пользоваться уже определёнными HTTP-статусами,
        # которые cодержат enum. Такой код будет более поддерживаемым.
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Popular films not found'
        )
    # Перекладываем данные из models.Film в Film.
    # Обратите внимание, что у модели бизнес-логики есть поле description,
    # которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и
    # формирования ответов API, вы бы предоставляли клиентам данные,
    # которые им не нужны, и, возможно, данные, которые опасно возвращать
    return [
        MovieShort(
            uuid=film.id,
            title=film.title,
            imdb_rating=film.imdb_rating
        ) for film in popular_films
    ]


@router.get('/', response_model=List[MovieShort])
async def film_general(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: str | None = None,
    genre: UUID | None = None,
    film_service: FilmService = Depends(get_film_service)
) -> List[MovieShort]:
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
        MovieShort(
            uuid=film.id,
            title=film.title,
            imdb_rating=film.imdb_rating
        ) for film in films
    ]


@router.get('/search', response_model=List[MovieShort])
async def film_search(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search_query: str | None = Query(None, alias="query"),
    film_service: FilmService = Depends(get_film_service)
) -> List[MovieShort]:
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
        MovieShort(
            uuid=film.id,
            title=film.title,
            imdb_rating=film.imdb_rating
        ) for film in films
    ]


# Внедряем FilmService с помощью Depends(get_film_service)
@router.get('/{film_id}', response_model=MovieFull)
async def film_details(
    film_id: str,
    film_service: FilmService = Depends(get_film_service)
) -> MovieFull:
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
    return MovieFull(
        uuid=film.id,
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        genre=[
            Genre(uuid=UUID(genre.id), name=genre.name)
            for genre in film.genres
        ],
        actors=[
            Person(uuid=UUID(actor.id), full_name=actor.name)
            for actor in film.actors
        ],
        directors=[
            Person(uuid=UUID(actor.id), full_name=actor.name)
            for actor in film.directors
        ],
        writers=[
            Person(uuid=UUID(actor.id), full_name=actor.name)
            for actor in film.writers
        ],
    )


@router.get('/{film_id}/similar', response_model=List[MovieShort])
async def film_similar(
    film_id: str,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    film_service: FilmService = Depends(get_film_service)
) -> List[MovieShort]:
    similar_films = await film_service.get_similar_by_id(
        film_id,
        page_number=page_number,
        page_size=page_size
    )
    if not similar_films:
        # Если фильм не найден, отдаём 404 статус.
        # Желательно пользоваться уже определёнными HTTP-статусами,
        # которые cодержат enum. Такой код будет более поддерживаемым.
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Similar films not found'
        )
    # Перекладываем данные из models.Film в Film.
    # Обратите внимание, что у модели бизнес-логики есть поле description,
    # которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и
    # формирования ответов API, вы бы предоставляли клиентам данные,
    # которые им не нужны, и, возможно, данные, которые опасно возвращать
    return [
        MovieShort(
            uuid=film.id,
            title=film.title,
            imdb_rating=film.imdb_rating
        ) for film in similar_films
    ]
