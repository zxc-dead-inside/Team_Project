from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
from src.models import Review, ReviewCreate, ReviewResponse, ReviewSearchResponse
from src.database import get_database


class ReviewService:
    def __init__(self):
        self.db = get_database()
        self.collection: AsyncIOMotorCollection = self.db.reviews

    async def create_review(self, review: ReviewCreate) -> ReviewResponse:
        """Создать рецензию"""
        # Проверяем, не существует ли уже рецензия от этого пользователя
        existing = await self.collection.find_one({
            "user_id": review.user_id,
            "film_id": review.film_id
        })
        
        if existing:
            raise ValueError("Review already exists for this user and film")
        
        review_doc = Review(**review.dict())
        result = await self.collection.insert_one(review_doc.dict(by_alias=True))
        
        created_review = await self.collection.find_one({"_id": result.inserted_id})
        return ReviewResponse(
            id=str(created_review["_id"]),
            user_id=created_review["user_id"],
            film_id=created_review["film_id"],
            text=created_review["text"],
            rating=created_review.get("rating"),
            created_at=created_review["created_at"],
            updated_at=created_review.get("updated_at")
        )

    async def get_film_reviews(self, film_id: str, skip: int = 0, limit: int = 10) -> ReviewSearchResponse:
        """Получить рецензии фильма с пагинацией"""
        # Подсчитываем общее количество
        total = await self.collection.count_documents({"film_id": film_id})
        
        # Получаем рецензии
        cursor = self.collection.find({"film_id": film_id}).sort("created_at", -1).skip(skip).limit(limit)
        reviews = []
        
        async for doc in cursor:
            reviews.append(ReviewResponse(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                film_id=doc["film_id"],
                text=doc["text"],
                rating=doc.get("rating"),
                created_at=doc["created_at"],
                updated_at=doc.get("updated_at")
            ))
        
        return ReviewSearchResponse(
            reviews=reviews,
            total=total,
            page=skip // limit + 1,
            size=limit
        )

    async def search_reviews(self, query: str, skip: int = 0, limit: int = 10) -> ReviewSearchResponse:
        """Поиск рецензий по тексту"""
        # Создаем текстовый поиск
        search_filter = {"$text": {"$search": query}}
        
        # Подсчитываем общее количество
        total = await self.collection.count_documents(search_filter)
        
        # Получаем рецензии
        cursor = self.collection.find(search_filter).sort("created_at", -1).skip(skip).limit(limit)
        reviews = []
        
        async for doc in cursor:
            reviews.append(ReviewResponse(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                film_id=doc["film_id"],
                text=doc["text"],
                rating=doc.get("rating"),
                created_at=doc["created_at"],
                updated_at=doc.get("updated_at")
            ))
        
        return ReviewSearchResponse(
            reviews=reviews,
            total=total,
            page=skip // limit + 1,
            size=limit
        )

    async def update_review(self, review_id: str, user_id: str, text: str, rating: int | None = None) -> ReviewResponse:
        """Обновить рецензию"""
        # Проверяем, что рецензия принадлежит пользователю
        existing = await self.collection.find_one({
            "_id": ObjectId(review_id),
            "user_id": user_id
        })
        
        if not existing:
            raise ValueError("Review not found or access denied")
        
        update_data = {
            "text": text,
            "updated_at": datetime.utcnow()
        }
        
        if rating is not None:
            update_data["rating"] = rating
        
        result = await self.collection.update_one(
            {"_id": ObjectId(review_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise ValueError("Failed to update review")
        
        updated_review = await self.collection.find_one({"_id": ObjectId(review_id)})
        return ReviewResponse(
            id=str(updated_review["_id"]),
            user_id=updated_review["user_id"],
            film_id=updated_review["film_id"],
            text=updated_review["text"],
            rating=updated_review.get("rating"),
            created_at=updated_review["created_at"],
            updated_at=updated_review.get("updated_at")
        )

    async def delete_review(self, review_id: str, user_id: str) -> bool:
        """Удалить рецензию"""
        result = await self.collection.delete_one({
            "_id": ObjectId(review_id),
            "user_id": user_id
        })
        
        return result.deleted_count > 0

    async def get_user_reviews(self, user_id: str) -> list[ReviewResponse]:
        """Получить все рецензии пользователя"""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        reviews = []
        
        async for doc in cursor:
            reviews.append(ReviewResponse(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                film_id=doc["film_id"],
                text=doc["text"],
                rating=doc.get("rating"),
                created_at=doc["created_at"],
                updated_at=doc.get("updated_at")
            ))
        
        return reviews 