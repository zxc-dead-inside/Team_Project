from typing import Any
from uuid import UUID

from pydantic import BaseModel


class FilmRoles(BaseModel):
    id: str
    roles: list[str]


class Person(BaseModel):
    id: UUID
    full_name: str
    films: list[FilmRoles]

    @property
    def cache_key(self) -> str:
        """Generate cache key for Redis."""
        return f"{self.__class__.__name__.lower()}:{self.id}"


async def serialize_person_list(es_response: dict[str, Any]) -> list[Person]:
    hits = es_response.get("hits", {}).get("hits", [])
    return [Person(**hit["_source"]) for hit in hits]


async def serialize_person_detail(es_doc: dict[str, Any]) -> Person:
    return Person(**es_doc["_source"])
