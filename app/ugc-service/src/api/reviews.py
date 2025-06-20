from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from ..models import ReviewCreate, ReviewResponse, ReviewSearchResponse
from ..services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


def get_review_service() -> ReviewService:
    return ReviewService()


@router.post("/", response_model=ReviewResponse, status_code=201)
async def create_review(
    review: ReviewCreate,
    service: ReviewService = Depends(get_review_service)
):
    """Создать рецензию"""
    try:
        return await service.create_review(review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/film/{film_id}", response_model=ReviewSearchResponse)
async def get_film_reviews(
    film_id: str,
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    service: ReviewService = Depends(get_review_service)
):
    """Получить рецензии фильма с пагинацией"""
    skip = (page - 1) * size
    return await service.get_film_reviews(film_id, skip, size)


@router.get("/search", response_model=ReviewSearchResponse)
async def search_reviews(
    query: str = Query(..., description="Поисковый запрос"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    service: ReviewService = Depends(get_review_service)
):
    """Поиск рецензий по тексту"""
    skip = (page - 1) * size
    return await service.search_reviews(query, skip, size)


@router.put("/{review_id}")
async def update_review(
    review_id: str,
    user_id: str = Query(..., description="ID пользователя"),
    text: str = Query(..., description="Новый текст рецензии"),
    rating: Optional[int] = Query(None, ge=1, le=10, description="Новая оценка"),
    service: ReviewService = Depends(get_review_service)
):
    """Обновить рецензию"""
    try:
        return await service.update_review(review_id, user_id, text, rating)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    user_id: str = Query(..., description="ID пользователя"),
    service: ReviewService = Depends(get_review_service)
):
    """Удалить рецензию"""
    deleted = await service.delete_review(review_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Review deleted successfully"}


@router.get("/user/{user_id}", response_model=List[ReviewResponse])
async def get_user_reviews(
    user_id: str,
    service: ReviewService = Depends(get_review_service)
):
    """Получить все рецензии пользователя"""
    return await service.get_user_reviews(user_id) 