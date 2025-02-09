from pydantic import BaseModel
from uuid import UUID


class FilmRoles(BaseModel):
    id: str
    roles: list[str]


class Person(BaseModel):
    id: UUID
    full_name: str
    films: list[FilmRoles]
