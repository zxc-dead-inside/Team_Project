import json
from datetime import timedelta

from core.config import settings
from models.movies_models import MovieDetailResponse, MovieShortListResponse
from services.cache.base import AbstractCacheStorage
from services.cache_services.base import AbstractFilmCacheService
from services.utils import UUIDEncoder


class FilmCacheService(AbstractFilmCacheService):
    def __init__(self, cache: AbstractCacheStorage):
        self.cache = cache

    async def get_film_from_cache(self, film_id: str) -> MovieDetailResponse | None:
        key = f"{settings.movie_index}:moviedetailresponse:{film_id}"

        data = await self.cache.get(key)
        if not data:
            return None
        film = MovieDetailResponse.model_validate_json(data)
        return film

    async def put_film_to_cache(
        self, film: MovieDetailResponse, ttl: timedelta = settings.default_ttl
    ):
        key = f"{settings.movie_index}:{film.cache_key}"
        await self.cache.set(key, film.model_dump_json(), ttl)

    async def get_films_from_cache(
        self, search_query: str
    ) -> list[MovieShortListResponse] | None:
        key = f"{settings.movie_index}:movieshortlistresponse_list:{search_query}"

        data = await self.cache.get(key)
        if not data:
            return None
        films = [MovieShortListResponse(**dict(item)) for item in json.loads(data)]
        return films

    async def put_films_to_cache(
        self,
        search_query: str,
        data: list[MovieShortListResponse],
        ttl: timedelta = settings.default_ttl,
    ):
        key = (
            f"{settings.movie_index}:"
            f"{data[0].__class__.__name__.lower()}_list:{search_query}"
        )

        films = json.dumps([item.__dict__ for item in data], cls=UUIDEncoder)
        await self.cache.set(key, films, ttl)
