from pydantic import BaseModel
from uuid import UUID


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
