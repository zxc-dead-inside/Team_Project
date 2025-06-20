from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models import BookmarkCreate, BookmarkResponse
from ..services.bookmark_service import BookmarkService

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


def get_bookmark_service() -> BookmarkService:
    return BookmarkService()


@router.post("/", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(
    bookmark: BookmarkCreate,
    service: BookmarkService = Depends(get_bookmark_service)
):
    """Создать закладку"""
    try:
        return await service.create_bookmark(bookmark)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}", response_model=List[BookmarkResponse])
async def get_user_bookmarks(
    user_id: str,
    service: BookmarkService = Depends(get_bookmark_service)
):
    """Получить все закладки пользователя"""
    return await service.get_user_bookmarks(user_id)


@router.delete("/user/{user_id}/film/{film_id}")
async def delete_bookmark(
    user_id: str,
    film_id: str,
    service: BookmarkService = Depends(get_bookmark_service)
):
    """Удалить закладку"""
    deleted = await service.delete_bookmark(user_id, film_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"message": "Bookmark deleted successfully"}


@router.get("/user/{user_id}/film/{film_id}/exists")
async def check_bookmark_exists(
    user_id: str,
    film_id: str,
    service: BookmarkService = Depends(get_bookmark_service)
):
    """Проверить существование закладки"""
    exists = await service.check_bookmark_exists(user_id, film_id)
    return {"exists": exists} 