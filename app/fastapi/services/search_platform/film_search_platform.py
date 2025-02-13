
from uuid import UUID

from core.config import settings
from  models.movies_models import (
    MovieDetailResponse, MovieShortListResponse, serialize_movie_detail,
    serialize_movie_short_list)
from services.search_platform.base import AbstractSearchPlatfrom

class FilmSearchService:
    """"
    A service class responsible for retrieving movies data from search
    platform.
    """

    def __init__(self, search_platform: AbstractSearchPlatfrom):
        self.search_platform = search_platform
    
    async def get_film_from_search_platform(
            self, film_id: str) -> MovieDetailResponse | None:
        """Returns film by id."""

        doc = await self.search_platform.get(settings.movie_index, film_id)
        if doc is None:
            return None

        return await serialize_movie_detail(doc)
    
    async def search_film_in_search_platform(
            self, page_number: int, page_size: int, search_query: str = None
    ) -> list[MovieShortListResponse] | None:
        """Trying to get the data from the es."""

        query = {"bool": {"must": [{"match_all": {}}]}}
        skip = (page_number - 1) * page_size
        body = {
            "query": query,
            "from": skip,
            "size": page_size,
            "_source": ["id", "title", "description", "imdb_rating"],
        }
        if search_query:
            query["bool"]["must"] = [
                {
                    "multi_match": {
                        "query": search_query,
                        "fields": [
                            "title",
                            "description",
                            "actors_names",
                            "directors_names",
                            "writers_names",
                        ],
                        "type": "cross_fields",
                        "operator": "and",
                    }
                }
            ]
        body["sort"] = [{"imdb_rating": {"order": "desc"}}]

        results = await self.search_platform.search(index=settings.movie_index, body=body)
        
        if results is None:
            return None
        return await serialize_movie_short_list(results)

    async def search_film_general_in_search_platform(
            self, page_number: int, page_size: int, sort: str = None,
            genre: UUID = None) -> list[MovieShortListResponse] | None:
        """
        Search for movies in Elasticsearch with pagination, sorting, and 
        genre filtering.
        """

        query = {"bool": {"must": [{"match_all": {}}]}}
        skip = (page_number - 1) * page_size
        body = {
            "query": query,
            "from": skip,
            "size": page_size,
            "_source": ["id", "title", "imdb_rating"],
        }

        if sort:
            body["sort"] = [{
                sort.lstrip("-"): {
                    "order": "desc" if sort.startswith("-") else "asc"
                }
            }]
        if genre:
            query["bool"]["filter"] = [{
                "nested": {
                    "path": "genres",
                    "query": {
                        "term": {
                            "genres.id": genre
                        }
                    }
                }
            }]
        results = await self.search_platform.search(
            index=settings.movie_index,
            body=body
        )
        if results is None:
            return None
        return await serialize_movie_short_list(results)
