from pydantic import BaseModel
from typing import Any, List
from uuid import UUID


class FilmRoles(BaseModel):
    id: str
    roles: List[str]


class Person(BaseModel):
    id: UUID
    full_name: str
    films: List[FilmRoles]
