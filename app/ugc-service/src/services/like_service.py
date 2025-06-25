from motor.motor_asyncio import AsyncIOMotorCollection
from src.database import get_database
from src.models import Like, LikeCreate, LikeResponse, ReviewRatingResponse


class LikeService:
    def __init__(self):
        self.db = get_database()
        self.collection: AsyncIOMotorCollection = self.db.likes

    async def create_like(self, like: LikeCreate) -> LikeResponse:
        """Создать лайк/дизлайк для рецензии"""
        # Проверяем, что рейтинг соответствует требованиям (0 или 10)
        if like.rating not in [0, 10]:
            raise ValueError("Rating must be 0 (dislike) or 10 (like)")
        
        # Проверяем, не существует ли уже оценка от этого пользователя
        existing = await self.collection.find_one({
            "user_id": like.user_id,
            "review_id": like.review_id
        })
        
        if existing:
            # Обновляем существующую оценку
            result = await self.collection.update_one(
                {"user_id": like.user_id, "review_id": like.review_id},
                {"$set": {"rating": like.rating}}
            )
            updated_like = await self.collection.find_one({
                "user_id": like.user_id,
                "review_id": like.review_id
            })
        else:
            # Создаем новую оценку
            like_doc = Like(**like.dict())
            result = await self.collection.insert_one(like_doc.dict(by_alias=True))
            updated_like = await self.collection.find_one({"_id": result.inserted_id})
        
        return LikeResponse(
            id=str(updated_like["_id"]),
            user_id=updated_like["user_id"],
            review_id=updated_like["review_id"],
            rating=updated_like["rating"],
            created_at=updated_like["created_at"]
        )

    async def get_user_likes(self, user_id: str) -> list[LikeResponse]:
        """Получить все лайки пользователя"""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        likes = []
        
        async for doc in cursor:
            likes.append(LikeResponse(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                review_id=doc["review_id"],
                rating=doc["rating"],
                created_at=doc["created_at"]
            ))
        
        return likes

    async def get_review_rating(self, review_id: str) -> ReviewRatingResponse:
        """Получить статистику лайков/дизлайков для рецензии"""
        pipeline = [
            {"$match": {"review_id": review_id}},
            {"$group": {
                "_id": "$review_id",
                "likes_count": {"$sum": {"$cond": [{"$eq": ["$rating", 10]}, 1, 0]}},
                "dislikes_count": {"$sum": {"$cond": [{"$eq": ["$rating", 0]}, 1, 0]}},
                "total_votes": {"$sum": 1}
            }}
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        
        if result:
            return ReviewRatingResponse(
                review_id=review_id,
                likes_count=result[0]["likes_count"],
                dislikes_count=result[0]["dislikes_count"],
                total_votes=result[0]["total_votes"]
            )
        else:
            return ReviewRatingResponse(
                review_id=review_id,
                likes_count=0,
                dislikes_count=0,
                total_votes=0
            )

    async def delete_like(self, user_id: str, review_id: str) -> bool:
        """Удалить лайк/дизлайк"""
        result = await self.collection.delete_one({
            "user_id": user_id,
            "review_id": review_id
        })
        
        return result.deleted_count > 0

    async def get_user_rating_for_review(self, user_id: str, review_id: str) -> int | None:
        """Получить оценку пользователя для конкретной рецензии"""
        like = await self.collection.find_one({
            "user_id": user_id,
            "review_id": review_id
        })
        
        return like["rating"] if like else None 