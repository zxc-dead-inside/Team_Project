from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GenreBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class ElasticPersonNested(BaseModel):
    id: str
    name: str

# Response Models for API
class MovieListResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    imdb_rating: float | None = None
    genres: list[str]
    actors_names: list[str]
    directors_names: list[str]
    writers_names: list[str]
    
    model_config = ConfigDict(from_attributes=True)

class MovieDetailResponse(MovieListResponse):
    actors: list[ElasticPersonNested]
    directors: list[ElasticPersonNested]
    writers: list[ElasticPersonNested]
    
    model_config = ConfigDict(from_attributes=True)

# Serialization functions
async def serialize_movie_list(es_response: dict[str, Any]) -> list[MovieListResponse]:
    hits = es_response.get("hits", {}).get("hits", [])
    return [MovieListResponse(**hit["_source"]) for hit in hits]

async def serialize_movie_detail(es_doc: dict[str, Any]) -> MovieDetailResponse:
    return MovieDetailResponse(**es_doc["_source"])
