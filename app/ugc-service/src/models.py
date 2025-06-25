from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


# Модели для закладок
class BookmarkBase(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    film_id: str = Field(..., description="ID фильма")


class BookmarkCreate(BookmarkBase):
    pass


class Bookmark(BookmarkBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


# Модели для лайков
class LikeBase(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    review_id: str = Field(..., description="ID рецензии")
    rating: int = Field(..., description="Оценка: 10 - лайк, 0 - дизлайк")


class LikeCreate(LikeBase):
    pass


class Like(LikeBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


# Модели для рецензий
class ReviewBase(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    film_id: str = Field(..., description="ID фильма")
    text: str = Field(..., min_length=1, max_length=5000,
                      description="Текст рецензии")
    rating: int | None = Field(None, ge=1, le=10,
                                  description="Оценка от 1 до 10")


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


# Модели для ответов API
class BookmarkResponse(BaseModel):
    id: str
    user_id: str
    film_id: str
    created_at: datetime


class LikeResponse(BaseModel):
    id: str
    user_id: str
    review_id: str
    rating: int
    created_at: datetime


class ReviewResponse(BaseModel):
    id: str
    user_id: str
    film_id: str
    text: str
    rating: int | None
    created_at: datetime
    updated_at: datetime | None


class ReviewRatingResponse(BaseModel):
    review_id: str
    likes_count: int
    dislikes_count: int
    total_votes: int


class ReviewSearchResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int
    page: int
    size: int
