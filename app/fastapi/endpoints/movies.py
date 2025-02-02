from core.config import settings
from core.elasticsearch import es_client
from models.movies_models import (
    MovieDetailResponse,
    MovieListResponse,
    serialize_movie_detail,
    serialize_movie_list,
)

from fastapi import APIRouter, HTTPException, Query


router = APIRouter()


@router.get("/", response_model=list[MovieListResponse])
async def get_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort: str | None = None,
    search: str | None = None,
):
    try:
        query = {"bool": {"must": [{"match_all": {}}]}}

        if search:
            query["bool"]["must"] = [
                {
                    "multi_match": {
                        "query": search,
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

        body = {"query": query, "from": skip, "size": limit}

        if sort:
            body["sort"] = [{"imdb_rating": {"order": "desc"}}]

        response = await es_client.search(index=settings.MOVIE_INDEX, body=body)

        return await serialize_movie_list(response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{movie_id}", response_model=MovieDetailResponse)
async def get_movie(movie_id: str):
    try:
        response = await es_client.get(index=settings.MOVIE_INDEX, id=movie_id)
        return await serialize_movie_detail(response)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Movie not found") from e
