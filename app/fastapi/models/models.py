"""
Models for the movie database application.

This module contains Pydantic models for handling movie-related
data structures, including films, persons, genres, and search functionality.
"""

from datetime import UTC, datetime, timedelta
from functools import cached_property
from typing import Annotated, Literal, NewType, TypeAlias
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator
)

from core.elasticsearch import es_client
from core.config import settings


# Custom types
RoleType: TypeAlias = Literal["actor", "director", "writer"]
PersonName = NewType("PersonName", str)


class BaseAPIModel(BaseModel):
    """Base model with common configuration for all API models."""

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        strict=True,
        validate_assignment=True,
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )

    @property
    def cache_key(self) -> str:
        """Generate cache key for Redis."""
        return f"{self.__class__.__name__.lower()}:{self.uuid}"

    @property
    def cache_ttl(self) -> timedelta:
        """Default cache TTL."""
        return timedelta(hours=1)


class Genre(BaseAPIModel):
    """Genre model representing movie categories."""

    uuid: UUID = Field(
        description="Unique identifier for the genre",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    name: Annotated[str, StringConstraints(min_length=1, max_length=100)] = Field(
        description="Name of the genre",
        examples=["Action", "Drama", "Science Fiction"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Action",
            }
        }
    )


class PersonBase(BaseAPIModel):
    """Base model for person-related data."""

    uuid: UUID = Field(
        description="Unique identifier for the person",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    full_name: PersonName = Field(
        description="Full name of the person",
        examples=["John Doe", "Jane Smith"],
        max_length=255,
        min_length=1,
    )


class MovieRole(BaseAPIModel):
    """Model representing a person's role in a film."""

    uuid: UUID = Field(
        description="Unique identifier for the film",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    roles: list[RoleType] = Field(
        description="List of roles the person had in the film",
        min_length=1,
        examples=[["actor"], ["director", "writer"]],
    )

    @model_validator(mode="after")
    def validate_roles(self) -> "MovieRole":
        """Validate that roles are from allowed values."""
        allowed_roles = {"actor", "director", "writer"}
        if not all(role.lower() in allowed_roles for role in self.roles):
            raise ValueError(f"Invalid role. Allowed roles are: {allowed_roles}")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "roles": ["actor", "director"],
            }
        }


class Person(PersonBase):
    """Complete person model including filmography."""

    films: list[MovieRole] = Field(
        description="List of films the person was involved in",
        default_factory=list,
    )

    @cached_property
    def role_count(self) -> dict[RoleType, int]:
        """Count of each role type across all films."""
        counts: dict[RoleType, int] = {"actor": 0, "director": 0, "writer": 0}
        for film in self.films:
            for role in film.roles:
                counts[role] += 1
        return counts


class PersonShort(PersonBase):
    """Simplified person model for nested references in film details."""

    role_type: RoleType = Field(
        description="Primary role of the person in the film",
    )


class MovieShort(BaseAPIModel):
    """Simplified film model for lists and search results."""

    uuid: UUID = Field(
        description="Unique identifier for the film",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    title: Annotated[str, StringConstraints(min_length=1, max_length=255)] = Field(
        description="Title of the film",
        examples=["The Example Movie"],
    )
    imdb_rating: float = Field(
        description="IMDB rating of the film",
        ge=0,
        le=10,
        examples=[8.5],
    )


class MovieFull(MovieShort):
    """Complete film model with all details."""

    description: Annotated[str, StringConstraints(max_length=10000)] = Field(
        description="Detailed description of the film"
    )
    genre: list[str] = Field(
        description="List of film genres",
        min_length=1,
    )
    actors: list[PersonBase] = Field(
        description="Actors in the movie",
        default_factory=list,
    )
    writers: list[PersonBase] = Field(
        description="Writers in the movie",
        default_factory=list,
    )
    directors: list[PersonBase] = Field(
        description="Directors in the movie",
        min_length=1,
    )
    created_at: datetime = Field(
        description="Film creation timestamp",
        default_factory=lambda: datetime.now(UTC),
    )
    file_path: HttpUrl | None = Field(
        None,
        description="URL to the film file",
        examples=["https://example.com/movies/123.mp4"],
        json_schema_extra={
            "format": "uri",
            "pattern": "^https?://.*",
        },
    )

    @model_validator(mode="after")
    def validate_participants(self) -> "MovieFull":
        """Validate that film has at least one participant."""
        if not (self.actors or self.writers or self.directors):
            raise ValueError("Film must have at least one participant")
        return self

    @cached_property
    def participant_count(self) -> int:
        """Total number of unique participants."""
        return len(
            {
                person.uuid
                for group in (self.actors, self.writers, self.directors)
                for person in group
            }
        )

    @property
    def cache_ttl(self) -> timedelta:
        """Cache TTL for movies based on rating."""
        if self.imdb_rating >= 8.0:
            # Popular movies cached for shorter time
            return timedelta(hours=12)
        return timedelta(hours=24)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "title": "The Example Movie",
                "imdb_rating": 8.5,
                "description": "An amazing example movie...",
                "genre": ["Action", "Drama"],
                "created_at": "2024-01-01T00:00:00Z",
            }
        }
    )


class SearchParams(BaseAPIModel):
    """Base model for search parameters."""

    query: Annotated[
        str,
        StringConstraints(min_length=1, max_length=100)
    ] = Field(
        description="Search query string",
        examples=["star wars"],
    )
    page_number: int = Field(
        description="Page number for pagination",
        ge=1,
        default=1,
    )
    page_size: int = Field(
        description="Number of items per page",
        ge=1,
        le=100,
        default=50,
    )


class MovieSearch(SearchParams):
    """Film search parameters with additional filtering options."""

    genre_uuid: UUID | None = Field(
        None,
        description="Filter by genre UUID",
    )
    min_rating: float | None = Field(
        None,
        description="Minimum IMDB rating",
        ge=0,
        le=10,
    )
    release_year: int | None = Field(
        None,
        description="Filter by release year",
        ge=1888,  # First movie year
    )
    sort_by: Literal["rating", "title", "release_date"] = Field(
        default="rating",
        description="Field to sort results by",
    )
    order: Literal["asc", "desc"] = Field(
        default="desc",
        description="Sort order",
    )


class PersonSearch(SearchParams):
    """Person search parameters with role filtering."""

    role_type: RoleType | None = Field(
        None,
        description="Filter by person's role",
    )


class PaginatedResponse(BaseAPIModel):
    """Base model for paginated responses."""

    total: int = Field(
        description="Total number of items",
        ge=0,
    )
    page_number: int = Field(
        description="Current page number",
        ge=1,
    )
    page_size: int = Field(
        description="Number of items per page",
        ge=1,
    )


class MovieSearchResponse(PaginatedResponse):
    """Paginated response for film search."""

    items: list[MovieShort] = Field(description="List of films")


class PersonSearchResponse(PaginatedResponse):
    """Paginated response for person search."""

    items: list[Person] = Field(description="List of persons")


async def serialize_film_detail(response: dict) -> MovieFull:
    """Serialize film detail response."""
    film_data = response["_source"]

    film_data["uuid"] = UUID(film_data.pop("id"))
    film_data.pop("actors_names")
    film_data.pop("directors_names")
    film_data.pop("writers_names")

    genres = film_data.pop("genres")
    film_data["genre"] = []
    for genre_name in genres:
        search_response = await es_client.search(
            index=settings.GENRE_INDEX,
            body={
                "query": {
                    "match": {"name": genre_name}
                }
            }
        )

        hits = search_response["hits"]["hits"]
        if hits:
            genre_data = hits[0]["_source"]
            film_data["genre"].append({
                "uuid": UUID(genre_data["id"]),
                "name": genre_data["name"],
            })
        else:
            film_data["genre"].append({"uuid": None, "name": genre_name})

    for role in ["actors", "directors", "writers"]:
        if role in film_data:
            for person in film_data[role]:
                person["uuid"] = UUID(person.pop("id"))
                person["full_name"] = person.pop("name")

    return MovieFull(**film_data)
