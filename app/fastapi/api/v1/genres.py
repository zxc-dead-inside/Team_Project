from http import HTTPStatus
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.genre import GenreService, get_genre_service


router = APIRouter()


class Genre(BaseModel):
    uuid: UUID
    name: str


@router.get('/', response_model=List[Genre])
async def genre_list(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: str | None = None,
    genre_service: GenreService = Depends(get_genre_service)
) -> List[Genre]:
    genres = await genre_service.get_list(
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


@router.get('/{genre_id}', response_model=Genre)
async def get_by_id(
    genre_id: str,
    genre_service: GenreService = Depends(get_genre_service)
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
