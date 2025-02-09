from pydantic import BaseModel
from uuid import UUID


class Genre(BaseModel):
    id: UUID
    name: str

    @property
    def cache_key(self) -> str:
        """Generate cache key for Redis."""
        return f"{self.__class__.__name__.lower()}:{self.id}"
