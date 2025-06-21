from fastapi import APIRouter, HTTPException, Depends
from typing import List
from src.models import LikeCreate, LikeResponse, FilmRatingResponse
from src.services.like_service import LikeService

router = APIRouter(prefix="/likes", tags=["likes"])


def get_like_service() -> LikeService:
    return LikeService()


@router.post("/", response_model=LikeResponse, status_code=201)
async def create_like(
    like: LikeCreate,
    service: LikeService = Depends(get_like_service)
):
    """Создать лайк с оценкой"""
    try:
        return await service.create_like(like)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}", response_model=List[LikeResponse])
async def get_user_likes(
    user_id: str,
    service: LikeService = Depends(get_like_service)
):
    """Получить все лайки пользователя"""
    return await service.get_user_likes(user_id)


@router.get("/film/{film_id}/rating", response_model=FilmRatingResponse)
async def get_film_rating(
    film_id: str,
    service: LikeService = Depends(get_like_service)
):
    """Получить среднюю оценку фильма"""
    return await service.get_film_rating(film_id)


@router.delete("/user/{user_id}/film/{film_id}")
async def delete_like(
    user_id: str,
    film_id: str,
    service: LikeService = Depends(get_like_service)
):
    """Удалить лайк"""
    deleted = await service.delete_like(user_id, film_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Like not found")
    return {"message": "Like deleted successfully"}


@router.get("/user/{user_id}/film/{film_id}/rating")
async def get_user_rating_for_film(
    user_id: str,
    film_id: str,
    service: LikeService = Depends(get_like_service)
):
    """Получить оценку пользователя для конкретного фильма"""
    rating = await service.get_user_rating_for_film(user_id, film_id)
    if rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    return {"rating": rating} 