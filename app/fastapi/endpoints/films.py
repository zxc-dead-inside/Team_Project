from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from core.config import settings
from core.elasticsearch import es_client
from models.models import MovieSearchResponse, MovieShort, MovieFull


router = APIRouter()

@router.get("/search/", response_model=MovieSearchResponse)
async def get_films(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search_query: str | None = Query(None, alias="query"),
):
    try:
        query = {"bool": {"must": [{"match_all": {}}]}}

        skip = (page_number - 1) * page_size
        body = {
            "query": query,
            "from": skip,
            "size": page_size,
            "_source": ["id", "title", "imdb_rating"],
        }

        if search_query:
            query["bool"]["must"] = [
                {
                    "multi_match": {
                        "query": search_query,
                        "fields": [
                            "title^3",
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

        response = await es_client.search(index=settings.MOVIE_INDEX, body=body)

        total_hits = response["hits"].get("total", {}).get("value", 0)
        movies = [
            MovieShort(uuid=UUID(hit["_source"]["id"]), **hit["_source"])
            for hit in response["hits"]["hits"]
        ]

        return MovieSearchResponse(
            total=total_hits,
            page_number=page_number,
            page_size=page_size,
            items=movies,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{film_id}/", response_model=MovieFull)
async def get_movie(film_id: str):
    try:
        response = await es_client.get(index=settings.MOVIE_INDEX, id=film_id)
        return MovieFull(uuid=UUID(response["id"]), **response["_source"])

    except Exception as e:
        raise HTTPException(status_code=404, detail="Movie not found") from e


@router.get("", response_model=MovieSearchResponse)
async def get_films(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: str | None = None,
    genre: str | None = None,
):
    try:
        query = {"bool": {"must": [{"match_all": {}}]}}

        skip = (page_number - 1) * page_size
        body = {
            "query": query,
            "from": skip,
            "size": page_size,
            "_source": ["id", "title", "imdb_rating"],
        }

        if sort:
            sort_field = sort.lstrip("-")
            sort_order = "desc" if sort.startswith("-") else "asc"
            body["sort"] = [{sort_field: {"order": sort_order}}]

        if genre:
            query["bool"]["filter"] = [
                {"term": {"genres": str(genre)}}
            ]

        response = await es_client.search(index=settings.MOVIE_INDEX, body=body)

        total_hits = response["hits"].get("total", {}).get("value", 0)
        movies = [
            MovieShort(uuid=UUID(hit["_source"]["id"]), **hit["_source"])
            for hit in response["hits"]["hits"]
        ]

        return MovieSearchResponse(
            total=total_hits,
            page_number=page_number,
            page_size=page_size,
            items=movies,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))