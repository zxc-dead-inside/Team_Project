from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from models.models import MovieRole, MovieShort, Person, PersonBase
from services.base import AbstractService
from services.di import get_film_service, get_person_service

from fastapi import APIRouter, Depends, HTTPException, Query


router = APIRouter()


@router.get(
    "/",
    response_model=list[PersonBase],
    summary="Get list of persons",
    description=("Return list of persons, ids and names"),
)
async def persons_list(
    page_number: Annotated[
        int, Query(ge=1, description="Page number, must be >= 1")
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Number of items per page, must be between 1 and 100",
        ),
    ] = 10,
    sort: Annotated[str | None, Query(description="Sorting criteria, optional")] = None,
    person_service: AbstractService = Depends(get_person_service),
) -> list[PersonBase]:
    """Return list of persons."""

    persons = await person_service.search_query(
        page_number=page_number, page_size=page_size, sort=sort
    )
    if not persons:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Persons not found"
        )
    return [
        PersonBase(uuid=person.id, full_name=person.full_name) for person in persons
    ]


@router.get(
    "/search",
    response_model=list[Person],
    summary="Search persons",
    description="Return list of persons by search query",
)
async def persons_search(
    page_number: Annotated[
        int, Query(ge=1, description="Page number, must be >= 1")
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Number of items per page, must be between 1 and 100",
        ),
    ] = 10,
    query: Annotated[str | None, Query(description="Search query, optional")] = None,
    person_service: AbstractService = Depends(get_person_service),
) -> list[Person]:
    """Return searched list of persons."""

    persons = await person_service.search_query(
        page_number=page_number, page_size=page_size, search_query=query
    )
    if not persons:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Persons not found"
        )
    return [
        Person(
            uuid=person.id,
            full_name=person.full_name,
            films=[
                MovieRole(uuid=UUID(film.id), roles=film.roles) for film in person.films
            ],
        )
        for person in persons
    ]


@router.get(
    "/{person_id}",
    response_model=Person,
    summary="Get person's roles by id",
    description="Return persons roles in films by person id",
)
async def get_by_id(
    person_id: str, person_service: AbstractService = Depends(get_person_service)
) -> Person:
    """Retrun person by Person_id."""

    person = await person_service.get_by_id(person_id=person_id)
    if not person:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Persons not found"
        )
    return Person(
        uuid=person.id,
        full_name=person.full_name,
        films=[
            MovieRole(uuid=UUID(film.id), roles=film.roles) for film in person.films
        ],
    )


@router.get(
    "/{person_id}/film",
    response_model=list[MovieShort],
    summary="Get person's films by id",
    description="Return list of films by person id",
)
async def get_films_by_person_id(
    person_id: str,
    person_service: AbstractService = Depends(get_person_service),
    film_service: AbstractService = Depends(get_film_service),
) -> list[MovieShort]:
    """Retrun list of films with person by Person_id."""

    person = await person_service.get_by_id(person_id=person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Person not found")
    films = [await film_service.get_by_id(film_id=film.id) for film in person.films]
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Films by Person not found"
        )
    return [
        MovieShort(uuid=film.id, title=film.title, imdb_rating=film.imdb_rating)
        for film in films
    ]
