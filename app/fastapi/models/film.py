# Используем pydantic для упрощения работы при перегонке
# данных из json в объекты.
from pydantic import BaseModel


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
    genres: list[Genre]
    actors: list[Person]
    directors: list[Person]
    writers: list[Person]


class FilmGeneral(BaseModel):
    id: str
    title: str
    imdb_rating: float
