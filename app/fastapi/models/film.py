# Используем pydantic для упрощения работы при перегонке
# данных из json в объекты.

from models.person import Person
from pydantic import BaseModel
from typing import List


class Film(BaseModel):
    id: str
    title: str
    imdb_rating: float
    description: str
    genres: List[str]
    actors: List[Person]
    directors: List[Person]
    writers: List[Person]


class FilmSearch(BaseModel):
    id: str
    title: str
    imdb_rating: float


class FilmGeneral(BaseModel):
    id: str
    title: str
    imdb_rating: float
