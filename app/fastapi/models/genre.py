from typing import Any
from uuid import UUID

from pydantic import BaseModel


class Genre(BaseModel):
    id: UUID
    name: str

    @property
    def cache_key(self) -> str:
        """Generate cache key for Redis."""
        return f"{self.__class__.__name__.lower()}:{self.id}"


async def serialize_genre_detail(
        es_doc: dict[str, Any]) -> Genre:
    return Genre(**es_doc["_source"])

async def serialize_genres_list(
        es_response: dict[str, Any]) -> list[Genre]:
    hits = es_response.get("hits", {}).get("hits", [])
    return [Genre(**hit["_source"]) for hit in hits]
