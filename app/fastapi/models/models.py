from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# Base Models for DB
class GenreBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=200)


class Genre(GenreBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    birth_date: date | None = None
    biography: str | None = Field(None, max_length=1000)
    photo_url: HttpUrl | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Person(PersonBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


# Elasticsearch-specific nested models
class ElasticPersonNested(BaseModel):
    id: str  # UUID as string for ES
    name: str  # full name for ES


class MovieBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    original_title: str | None = Field(None, max_length=200)
    release_date: date
    description: str | None = Field(
        None, max_length=10000
    )  # matches ES 'description' field
    runtime: int | None = Field(None, ge=0)
    poster_url: HttpUrl | None = None
    imdb_id: str | None = Field(None, pattern=r"^tt\d{7,8}$")
    imdb_rating: float | None = Field(None, ge=0, le=10)  # matches ES field


class Movie(MovieBase):
    id: UUID
    genres: list[Genre] = []
    directors: list[Person] = []
    actors: list[Person] = []
    writers: list[Person] = []

    model_config = ConfigDict(from_attributes=True)


# Elasticsearch Movie Document Model
class MovieElastic(BaseModel):
    id: str  # UUID as string for ES
    imdb_rating: float | None = None
    title: str
    description: str | None = None
    actors_names: list[str] = []  # Flattened list of actor names
    writers_names: list[str] = []  # Flattened list of writer names
    directors_names: list[str] = []  # Flattened list of director names
    genres: list[str] = []  # List of genre names
    actors: list[ElasticPersonNested] = []
    directors: list[ElasticPersonNested] = []
    writers: list[ElasticPersonNested] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_movie(cls, movie: Movie) -> "MovieElastic":
        return cls(
            id=str(movie.id),
            imdb_rating=movie.imdb_rating,
            title=movie.title,
            description=movie.description,
            actors_names=[person.full_name for person in movie.actors],
            writers_names=[person.full_name for person in movie.writers],
            directors_names=[person.full_name for person in movie.directors],
            genres=[genre.name for genre in movie.genres],
            actors=[
                ElasticPersonNested(id=str(actor.id), name=actor.full_name)
                for actor in movie.actors
            ],
            directors=[
                ElasticPersonNested(id=str(director.id), name=director.full_name)
                for director in movie.directors
            ],
            writers=[
                ElasticPersonNested(id=str(writer.id), name=writer.full_name)
                for writer in movie.writers
            ],
        )


# Create/Update Models
class GenreCreate(GenreBase):
    pass


class GenreUpdate(GenreBase):
    name: str | None = Field(None, min_length=1, max_length=50)


class PersonCreate(PersonBase):
    pass


class PersonUpdate(PersonBase):
    first_name: str | None = Field(None, min_length=1, max_length=50)
    last_name: str | None = Field(None, min_length=1, max_length=50)


class MovieCreate(MovieBase):
    genre_ids: list[UUID] = []
    director_ids: list[UUID] = []
    actor_ids: list[UUID] = []
    writer_ids: list[UUID] = []


class MovieUpdate(MovieBase):
    title: str | None = Field(None, min_length=1, max_length=200)
    original_title: str | None = None
    release_date: date | None = None
    genre_ids: list[UUID] | None = None
    director_ids: list[UUID] | None = None
    actor_ids: list[UUID] | None = None
    writer_ids: list[UUID] | None = None


# Response Models
class GenreResponse(Genre):
    movies_count: int = 0


class PersonResponse(Person):
    directed_movies: list[Movie] = []
    acted_movies: list[Movie] = []
    written_movies: list[Movie] = []


class MovieResponse(Movie):
    average_rating: float | None = Field(None, ge=0, le=10)
    ratings_count: int = 0
