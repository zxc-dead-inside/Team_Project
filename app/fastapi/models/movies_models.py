from datetime import timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Genre(BaseModel):
    id: UUID
    name: str = Field(..., min_length=1, max_length=50)

class ElasticPersonNested(BaseModel):
    id: UUID
    name: str

# Response Models for API
class MovieShortListResponse(BaseModel):
    id: UUID
    title: str
    imdb_rating: float | None = None
    
    model_config = ConfigDict(from_attributes=True)

class MovieListResponse(MovieShortListResponse):
    description: str | None = None
    genres: list[Genre]  # list[str]
    actors_names: list[str]
    directors_names: list[str]
    writers_names: list[str]
    
    model_config = ConfigDict(from_attributes=True)

class MovieDetailResponse(MovieListResponse):
    actors: list[ElasticPersonNested]
    directors: list[ElasticPersonNested]
    writers: list[ElasticPersonNested]
    
    model_config = ConfigDict(from_attributes=True)

    @property
    def cache_key(self) -> str:
        """Generate cache key for Redis."""
        return f"{self.__class__.__name__.lower()}:{self.id}"

    @property
    def cache_ttl(self) -> timedelta:
        """Default cache TTL."""
        return timedelta(hours=1)

# Serialization functions
async def serialize_movie_short_list(
        es_response: dict[str, Any]) -> list[MovieShortListResponse]:
    hits = es_response.get("hits", {}).get("hits", [])
    return [MovieShortListResponse(**hit["_source"]) for hit in hits]

async def serialize_movie_list(
        es_response: dict[str, Any]) -> list[MovieListResponse]:
    hits = es_response.get("hits", {}).get("hits", [])
    return [MovieListResponse(**hit["_source"]) for hit in hits]

async def serialize_movie_detail(
        es_doc: dict[str, Any]) -> MovieDetailResponse:
    return MovieDetailResponse(**es_doc["_source"])
