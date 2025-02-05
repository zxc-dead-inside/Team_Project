from http import HTTPStatus
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.person import PersonService, get_person_service
from services.film import FilmService, get_film_service


router = APIRouter()


class FilmRole(BaseModel):
    uuid: UUID
    roles: List[str]


class Person(BaseModel):
    uuid: UUID
    full_name: str


class PersonFilms(Person):
    films: List[FilmRole]


class Film(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float


@router.get('/', response_model=List[Person])
async def persons_list(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: str | None = None,
    person_service: PersonService = Depends(get_person_service)
) -> List[Person]:
    persons = await person_service.get_list(
        page_number=page_number,
        page_size=page_size,
        sort=sort
    )
    if not persons:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Persons not found'
        )
    return [
        Person(
            uuid=person.id,
            full_name=person.full_name
        ) for person in persons
    ]


@router.get('/search', response_model=List[PersonFilms])
async def persons_search(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    query: str = None,
    person_service: PersonService = Depends(get_person_service)
) -> List[PersonFilms]:
    persons = await person_service.search_query(
        page_number=page_number,
        page_size=page_size,
        search_query=query
    )
    if not persons:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Persons not found'
        )
    return [
        PersonFilms(
            uuid=person.id,
            full_name=person.full_name,
            films=[
                FilmRole(uuid=film.id, roles=film.roles)
                for film in person.films
            ]
        ) for person in persons
    ]


@router.get('/{person_id}', response_model=PersonFilms)
async def get_by_id(
    person_id: str,
    person_service: PersonService = Depends(get_person_service)
) -> PersonFilms:
    person = await person_service.get_by_id(
        person_id=person_id
    )
    if not person:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Persons not found'
        )
    return PersonFilms(
        uuid=person.id,
        full_name=person.full_name,
        films=[
            FilmRole(uuid=film.id, roles=film.roles)
            for film in person.films
        ]
    )


@router.get('/{person_id}/film', response_model=List[Film])
async def get_films_by_person_id(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
    film_service: FilmService = Depends(get_film_service)
) -> Film:
    person = await person_service.get_by_id(
        person_id=person_id
    )
    if not person:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Person not found'
        )
    films = [
        await film_service.get_by_id(film_id=film.id) for film in person.films
    ]
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Films by Person not found'
        )
    return [
        Film(
            uuid=film.id,
            title=film.title,
            imdb_rating=film.imdb_rating
        ) for film in films
    ]
