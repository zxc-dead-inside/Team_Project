# Используем pydantic для упрощения работы при перегонке
# данных из json в объекты.
from pydantic import BaseModel
from typing import List


class Person(BaseModel):
    id: str
    name: str


class Genre(BaseModel):
    id: str
    name: str


class Film(BaseModel):
    id: str
    title: str
    imdb_rating: float
    description: str
    genres: List[Genre]
    actors: List[Person]
    directors: List[Person]
    writers: List[Person]


class FilmGeneral(BaseModel):
    id: str
    title: str
    imdb_rating: float
