from uuid import UUID

from pydantic import BaseModel


class Person(BaseModel):
    id: UUID
    name: str

class Movie(BaseModel):
    id: UUID
    imdb_rating: float | None
    genres: list[str]
    title: str
    description: str | None
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[Person]
    actors: list[Person]
    writers: list[Person]