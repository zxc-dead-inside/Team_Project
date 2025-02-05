from pydantic import BaseModel
from typing import List


class FilmRoles(BaseModel):
    id: str
    roles: List[str]


class Person(BaseModel):
    id: str
    full_name: str
    films: List[FilmRoles]
