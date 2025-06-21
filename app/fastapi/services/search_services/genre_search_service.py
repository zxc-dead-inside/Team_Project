from elasticsearch import NotFoundError

from core.config import settings
from models.genre import Genre, serialize_genres_list, serialize_genre_detail
from services.search_platform.base import AbstractSearchPlatfrom


class GenreSearchSerivce:
    """"
    A service class responsible for retrieving genre data from search
    platform.
    """

    def __init__(self, search_platform: AbstractSearchPlatfrom):
        self.search_platform = search_platform
    

    async def get_genre_from_search_platform(
            self, genre_id: str) -> Genre | None:
        """Returns genre by genre_id."""

        result = await self.search_platform.get(settings.genre_index, genre_id)
        if result is None:
            return None
        return await serialize_genre_detail(result)

    async def get_genres_in_search_platform(
            self, page_number: int, page_size: int,
            sort: str | None = None) -> list[Genre] | None:
        """Returns list of genres."""

        skip = (page_number - 1) * page_size
        body = {
            "from": skip,
            "size": page_size,
            "_source": ["id", "name"],
        }
        if sort:
            body["sort"] = [{
                sort.lstrip("-"): {
                    "order": "desc" if sort.startswith("-") else "asc"
                }
            }]
        try:
            results = await self.search_platform.search(
                index=settings.genre_index,
                body=body
            )
        except NotFoundError:
            return None
        return await serialize_genres_list(results)
