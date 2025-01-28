from typing import Optional
from fastapi import APIRouter, HTTPException, Query
# from app.models.movie import MovieResponse, MovieCreate, MovieUpdate, MovieElastic
from v1.models import MovieResponse
from configs.elasticsearch import es_client
from configs.config import settings


router = APIRouter()

@router.get("/", response_model=list[MovieResponse])
async def get_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort: Optional[str] = None,
    search: Optional[str] = None
):
    try:
        query = {
            "bool": {
                "must": [{"match_all": {}}]
            }
        }
        
        if search:
            query["bool"]["must"] = [{
                "multi_match": {
                    "query": search,
                    "fields": ["title^3", "description", "actors_names", "directors_names", "writers_names"],
                    "type": "cross_fields",
                    "operator": "and"
                }
            }]
        
        body = {
            "query": query,
            "from": skip,
            "size": limit
        }
        
        if sort:
            body["sort"] = [{"imdb_rating": {"order": "desc"}}]
        
        response = await es_client.search(
            index=settings.MOVIE_INDEX,
            body=body
        )
        
        return [hit["_source"] for hit in response["hits"]["hits"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: str):
    try:
        response = await es_client.get(
            index=settings.MOVIE_INDEX,
            id=movie_id
        )
        return response["_source"]
    except Exception as e:
        raise HTTPException(status_code=404, detail="Movie not found")
