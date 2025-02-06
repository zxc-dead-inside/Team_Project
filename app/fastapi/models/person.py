from pydantic import BaseModel
from typing import List
from uuid import UUID


class FilmRoles(BaseModel):
    id: str
    roles: List[str]


class Person(BaseModel):
    id: UUID
    full_name: str
#    films: List[FilmRoles]

class PersonF(Person):
   films: List[FilmRoles]
