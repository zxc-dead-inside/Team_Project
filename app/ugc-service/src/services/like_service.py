from motor.motor_asyncio import AsyncIOMotorCollection
from typing import List, Optional
from bson import ObjectId
from ..models import Like, LikeCreate, LikeResponse, FilmRatingResponse
from ..database import get_database


class LikeService:
    def __init__(self):
        self.db = get_database()
        self.collection: AsyncIOMotorCollection = self.db.likes

    async def create_like(self, like: LikeCreate) -> LikeResponse:
        """Создать лайк с оценкой"""
        # Проверяем, не существует ли уже оценка от этого пользователя
        existing = await self.collection.find_one({
            "user_id": like.user_id,
            "film_id": like.film_id
        })
        
        if existing:
            # Обновляем существующую оценку
            result = await self.collection.update_one(
                {"user_id": like.user_id, "film_id": like.film_id},
                {"$set": {"rating": like.rating}}
            )
            updated_like = await self.collection.find_one({
                "user_id": like.user_id,
                "film_id": like.film_id
            })
        else:
            # Создаем новую оценку
            like_doc = Like(**like.dict())
            result = await self.collection.insert_one(like_doc.dict(by_alias=True))
            updated_like = await self.collection.find_one({"_id": result.inserted_id})
        
        return LikeResponse(
            id=str(updated_like["_id"]),
            user_id=updated_like["user_id"],
            film_id=updated_like["film_id"],
            rating=updated_like["rating"],
            created_at=updated_like["created_at"]
        )

    async def get_user_likes(self, user_id: str) -> List[LikeResponse]:
        """Получить все лайки пользователя"""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        likes = []
        
        async for doc in cursor:
            likes.append(LikeResponse(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                film_id=doc["film_id"],
                rating=doc["rating"],
                created_at=doc["created_at"]
            ))
        
        return likes

    async def get_film_rating(self, film_id: str) -> FilmRatingResponse:
        """Получить среднюю оценку фильма"""
        pipeline = [
            {"$match": {"film_id": film_id}},
            {"$group": {
                "_id": "$film_id",
                "average_rating": {"$avg": "$rating"},
                "total_ratings": {"$sum": 1}
            }}
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        
        if result:
            return FilmRatingResponse(
                film_id=film_id,
                average_rating=round(result[0]["average_rating"], 2),
                total_ratings=result[0]["total_ratings"]
            )
        else:
            return FilmRatingResponse(
                film_id=film_id,
                average_rating=0.0,
                total_ratings=0
            )

    async def delete_like(self, user_id: str, film_id: str) -> bool:
        """Удалить лайк"""
        result = await self.collection.delete_one({
            "user_id": user_id,
            "film_id": film_id
        })
        
        return result.deleted_count > 0

    async def get_user_rating_for_film(self, user_id: str, film_id: str) -> Optional[int]:
        """Получить оценку пользователя для конкретного фильма"""
        like = await self.collection.find_one({
            "user_id": user_id,
            "film_id": film_id
        })
        
        return like["rating"] if like else None 