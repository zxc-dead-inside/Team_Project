from motor.motor_asyncio import AsyncIOMotorCollection
from src.models import Bookmark, BookmarkCreate, BookmarkResponse
from src.database import get_database


class BookmarkService:
    def __init__(self):
        self.db = get_database()
        self.collection: AsyncIOMotorCollection = self.db.bookmarks

    async def create_bookmark(self, bookmark: BookmarkCreate) -> BookmarkResponse:
        """Создать закладку"""
        # Проверяем, не существует ли уже такая закладка
        existing = await self.collection.find_one({
            "user_id": bookmark.user_id,
            "film_id": bookmark.film_id
        })
        
        if existing:
            raise ValueError("Bookmark already exists")
        
        bookmark_doc = Bookmark(**bookmark.dict())
        result = await self.collection.insert_one(bookmark_doc.dict(by_alias=True))
        
        created_bookmark = await self.collection.find_one({"_id": result.inserted_id})
        return BookmarkResponse(
            id=str(created_bookmark["_id"]),
            user_id=created_bookmark["user_id"],
            film_id=created_bookmark["film_id"],
            created_at=created_bookmark["created_at"]
        )

    async def get_user_bookmarks(self, user_id: str) -> list[BookmarkResponse]:
        """Получить все закладки пользователя"""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        bookmarks = []
        
        async for doc in cursor:
            bookmarks.append(BookmarkResponse(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                film_id=doc["film_id"],
                created_at=doc["created_at"]
            ))
        
        return bookmarks

    async def delete_bookmark(self, user_id: str, film_id: str) -> bool:
        """Удалить закладку"""
        result = await self.collection.delete_one({
            "user_id": user_id,
            "film_id": film_id
        })
        
        return result.deleted_count > 0

    async def check_bookmark_exists(self, user_id: str, film_id: str) -> bool:
        """Проверить существование закладки"""
        bookmark = await self.collection.find_one({
            "user_id": user_id,
            "film_id": film_id
        })
        return bookmark is not None 