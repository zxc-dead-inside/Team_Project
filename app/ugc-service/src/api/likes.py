from fastapi import APIRouter, HTTPException, Depends
from typing import List
from src.models import LikeCreate, LikeResponse, ReviewRatingResponse
from src.services.like_service import LikeService

router = APIRouter(prefix="/likes", tags=["likes"])


def get_like_service() -> LikeService:
    return LikeService()


@router.post("/", response_model=LikeResponse, status_code=201)
async def create_like(
    like: LikeCreate,
    service: LikeService = Depends(get_like_service)
):
    """Создать лайк/дизлайк для рецензии"""
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


@router.get("/review/{review_id}/rating", response_model=ReviewRatingResponse)
async def get_review_rating(
    review_id: str,
    service: LikeService = Depends(get_like_service)
):
    """Получить статистику лайков/дизлайков для рецензии"""
    return await service.get_review_rating(review_id)


@router.delete("/user/{user_id}/review/{review_id}")
async def delete_like(
    user_id: str,
    review_id: str,
    service: LikeService = Depends(get_like_service)
):
    """Удалить лайк/дизлайк"""
    deleted = await service.delete_like(user_id, review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Like not found")
    return {"message": "Like deleted successfully"}


@router.get("/user/{user_id}/review/{review_id}/rating")
async def get_user_rating_for_review(
    user_id: str,
    review_id: str,
    service: LikeService = Depends(get_like_service)
):
    """Получить оценку пользователя для конкретной рецензии"""
    rating = await service.get_user_rating_for_review(user_id, review_id)
    if rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    return {"rating": rating} 