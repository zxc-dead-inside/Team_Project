from http import HTTPStatus
from typing import Annotated

from models.models import Genre
from services.base import AbstractService
from services.di import get_genre_service

from fastapi import APIRouter, Depends, HTTPException, Query


router = APIRouter()


@router.get(
    '/',
    response_model=list[Genre],
    summary="Get list of genres",
    description="Return list of  all genres"
)
async def genre_list(
    page_number: Annotated[
        int, Query(ge=1, description="Page number, must be >= 1")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100,
        description="Number of items per page, must be between 1 and 100")] = 10,
    sort: Annotated[str | None, Query(
        description="Sorting criteria, optional")] = None,
    genre_service: AbstractService = Depends(get_genre_service)
) -> list[Genre]:
    genres = await genre_service.search_query(
        page_number=page_number,
        page_size=page_size,
        sort=sort
    )
    if not genres:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Genres not found'
        )
    return [
        Genre(
            uuid=genre.id,
            name=genre.name
        ) for genre in genres
    ]


@router.get(
    '/{genre_id}',
    response_model=Genre,
    summary="Get genre by id",
    description="Return genre full data by id"
)
async def get_by_id(
    genre_id: str,
    genre_service: AbstractService = Depends(get_genre_service)
) -> Genre:
    genre = await genre_service.get_by_id(
        genre_id=genre_id
    )
    if not genre:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Genre not found'
        )
    return Genre(uuid=genre.id, name=genre.name)
