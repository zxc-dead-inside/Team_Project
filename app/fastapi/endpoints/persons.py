from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from models.models import Person, PersonBase, MovieRole, MovieShort
from services.film import FilmService, get_film_service
from services.person import PersonService, get_person_service



router = APIRouter()


@router.get('/', response_model=list[PersonBase])
async def persons_list(
    page_number: Annotated[
        int, Query(ge=1, description="Page number, must be >= 1")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100,
        description="Number of items per page, must be between 1 and 100")] = 10,
    sort: Annotated[str | None, Query(
        description="Sorting criteria, optional")] = None,
    person_service: PersonService = Depends(get_person_service)
) -> list[PersonBase]:
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
        PersonBase(
            uuid=person.id,
            full_name=person.full_name
        ) for person in persons
    ]


@router.get('/search', response_model=list[Person])
async def persons_search(
    page_number: Annotated[
        int, Query(ge=1, description="Page number, must be >= 1")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100,
        description="Number of items per page, must be between 1 and 100")] = 10,
    query: Annotated[
        str | None, Query(description="Search query, optional")] = None,
    person_service: PersonService = Depends(get_person_service)
) -> list[Person]:
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
        Person(
            uuid=person.id,
            full_name=person.full_name,
            films=[
                MovieRole(uuid=UUID(film.id), roles=film.roles)
                for film in person.films
            ]
        ) for person in persons
    ]


@router.get('/{person_id}', response_model=Person)
async def get_by_id(
    person_id: str,
    person_service: PersonService = Depends(get_person_service)
) -> Person:
    person = await person_service.get_by_id(person_id=person_id)
    if not person:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Persons not found'
        )
    return Person(
        uuid=person.id,
        full_name=person.full_name,
        films=[
            MovieRole(uuid=UUID(film.id), roles=film.roles)
            for film in person.films
        ]
    )


@router.get('/{person_id}/film', response_model=list[MovieShort])
async def get_films_by_person_id(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
    film_service: FilmService = Depends(get_film_service)
) -> list[MovieShort]:
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
        MovieShort(
            uuid=film.id,
            title=film.title,
            imdb_rating=film.imdb_rating
        ) for film in films
    ]
