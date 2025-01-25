import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List
from uuid import UUID

# type: ignore[arg-type]


@dataclass
class BaseDataSet:
    """Базовый датасет для id и updated_at полей."""
    id: str
    updated_at: dt.datetime

    def __post_init__(self):
        if isinstance(self.id, UUID):
            self.id = str(self.id)

    def people_to_list(
            self, people: List[Dict[str, str]],
            key: str) -> List[str]:
        return [person[key] for person in people]


@dataclass
class PeopleFilmWorks(BaseDataSet):
    """
    Хранит необходимую информацию об участниках фильмов и сериалов
    для загрузки в es.
    """
    actors: List[Dict[str, Any]]
    directors: List[Dict[str, Any]]
    writers: List[Dict[str, Any]]

    def get_fields(
            self
            ) -> List[str | List[str] | List[Dict[str, Any]]]:
        return [
            self.id,
            self.people_to_list(self.directors, 'name'),
            self.people_to_list(self.actors, 'name'),
            self.people_to_list(self.writers, 'name'),
            self.directors,
            self.actors,
            self.writers,
        ]


@dataclass
class GenreFilmWorks(BaseDataSet):
    """
    Хранит необходимую информацию по жанрам фильмов и сериалов для
    загрузки в es.
    """
    genres: List[str]

    def get_fields(self) -> List[str | List[str]]:
        return [
            self.id,
            list(self.genres)
        ]


@dataclass
class FilmWorkChanged(BaseDataSet):
    """
    Хранит необходимые полня при изменении в film_work.
    """

    title: str
    description: str
    rating: float
    type: str
    updated_at: dt.datetime

    def get_fields(self):
        return (
            self.id,
            self.title,
            self.description,
            self.rating,
            self.type
        )


@dataclass
class FilmWorkPopulate(BaseDataSet):
    """
    Хранит всю необходимую информацию по фильмам и сериалам для
    загрузки в es.
    """

    title: str
    description: str
    rating: float
    type: str
    created_at: dt.datetime
    updated_at: dt.datetime
    actors: List[Dict[str, Any]]
    directors: List[Dict[str, Any]]
    writers: List[Dict[str, Any]]
    genres: List[str]

    def get_fields(
            self) -> List[
                float | str | List[str] | List[Dict[str, Any]]]:
        return [
            self.id,
            self.rating,
            self.genres,
            self.title,
            self.description,
            self.people_to_list(self.directors, 'name'),
            self.people_to_list(self.actors, 'name'),
            self.people_to_list(self.writers, 'name'),
            self.directors,
            self.actors,
            self.writers,
        ]


@dataclass
class DataStructs:
    base_dataset: BaseDataSet
    get_film_work_populate: FilmWorkPopulate
    get_film_work_changed: FilmWorkChanged
    get_people_fw: PeopleFilmWorks
    get_genres_fw: GenreFilmWorks
