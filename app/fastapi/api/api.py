
from endpoints import movies, genres, persons  # films  # , 

from fastapi import APIRouter


api_router = APIRouter()

api_router.include_router(movies.router, prefix="/movies", tags=["movies"])
# api_router.include_router(films.router, prefix="/films", tags=["films"])
api_router.include_router(genres.router, prefix="/genres", tags=["genres"])
api_router.include_router(persons.router, prefix="/persons", tags=["people"])