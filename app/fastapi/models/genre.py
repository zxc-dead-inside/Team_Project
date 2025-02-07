from pydantic import BaseModel
from uuid import UUID


class Genre(BaseModel):
    id: UUID
    name: str
