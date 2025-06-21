import asyncio
import json
from pathlib import Path
from typing import Any

import asyncpg
from elasticsearch import AsyncElasticsearch
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import Settings
from .logger_setup import logger


class ETLState:
    """Manages the state of the ETL process."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.last_processed_id: int | None = None
        self.load_state()

    def load_state(self) -> None:
        """Load the last processed ID from the state file."""
        try:
            if self.file_path.exists():
                with open(self.file_path) as f:
                    state = json.load(f)
                    self.last_processed_id = state.get("last_processed_id")
                    logger.info(
                        "Loaded state: last_processed_id ="
                        f" {self.last_processed_id}"
                    )
        except Exception as e:
            logger.error(f"Error loading state: {e}")

    def save_state(self, last_id: int) -> None:
        """Save the last processed ID to the state file."""
        try:
            with open(self.file_path, "w") as f:
                json.dump({"last_processed_id": last_id}, f)
            self.last_processed_id = last_id
            logger.info(f"Saved state: last_processed_id = {last_id}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")


class MovieETL:
    """Main ETL class for transferring movie data from PostgreSQL to Elasticsearch."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.state = ETLState(settings.STATE_FILE_PATH)
        self.es_client = AsyncElasticsearch(
            hosts=[f"{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"]
        )

    async def init_postgres_pool(self):
        """Initialize PostgreSQL connection pool."""
        logger.info("self.settings.postgres_dsn: ", self.settings.postgres_dsn)
        self.pg_pool = await asyncpg.create_pool(str(self.settings.postgres_dsn))
        logger.info("self.pg_pool: ", self.pg_pool)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def fetch_movies_batch(
        self, last_id: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Fetch a batch of movies from PostgreSQL.

        Args:
            last_id: The ID of the last processed movie

        Returns:
            List of movies with their related data
        """
        query = """
        SELECT 
            m.id,
            m.title,
            m.description,
            m.rating as imdb_rating,
            ARRAY_AGG(DISTINCT g.name) as genres,
            ARRAY_AGG(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name)) FILTER (WHERE pfw.role = 'director') as directors,
            ARRAY_AGG(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name)) FILTER (WHERE pfw.role = 'actor') as actors,
            ARRAY_AGG(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name)) FILTER (WHERE pfw.role = 'writer') as writers
        FROM content.film_work m
        LEFT JOIN content.genre_film_work gfw ON m.id = gfw.film_work_id
        LEFT JOIN content.genre g ON gfw.genre_id = g.id
        LEFT JOIN content.person_film_work pfw ON m.id = pfw.film_work_id
        LEFT JOIN content.person p ON pfw.person_id = p.id
        WHERE ($1::uuid IS NULL OR m.id > $1)
        GROUP BY m.id
        ORDER BY m.id
        LIMIT $2
        """

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(query, last_id, self.settings.BATCH_SIZE)
            return [dict(row) for row in rows]

    def transform_movie(self, movie: dict[str, Any]) -> dict[str, Any]:
        """
        Transform movie data to match Elasticsearch schema.

        Args:
            movie: Raw movie data from PostgreSQL

        Returns:
            Transformed movie document for Elasticsearch
        """
        # Extract names for text search fields
        directors_names = [d["name"] for d in movie["directors"] if d]
        actors_names = [a["name"] for a in movie["actors"] if a]
        writers_names = [w["name"] for w in movie["writers"] if w]

        return {
            "id": str(movie["id"]),
            "imdb_rating": float(movie["imdb_rating"])
            if movie["imdb_rating"]
            else None,
            "genres": movie["genres"],
            "title": movie["title"],
            "description": movie["description"],
            "directors_names": directors_names,
            "actors_names": actors_names,
            "writers_names": writers_names,
            "directors": movie["directors"],
            "actors": movie["actors"],
            "writers": movie["writers"],
        }

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def load_to_elasticsearch(self, movies: list[dict[str, Any]]) -> None:
        """
        Load transformed movies to Elasticsearch.

        Args:
            movies: List of transformed movie documents
        """
        if not movies:
            return

        actions = []
        for movie in movies:
            actions.extend([{"index": {"_index": "movies", "_id": movie["id"]}}, movie])

        await self.es_client.bulk(operations=actions, refresh=True)
        logger.info(f"Loaded {len(movies)} movies to Elasticsearch")

    async def run(self) -> None:
        """Main ETL process."""
        try:
            await self.init_postgres_pool()

            while True:
                movies = await self.fetch_movies_batch(self.state.last_processed_id)

                if not movies:
                    logger.info("No more movies to process")
                    break

                transformed_movies = [self.transform_movie(movie) for movie in movies]
                await self.load_to_elasticsearch(transformed_movies)

                last_movie_id = movies[-1]["id"]
                self.state.save_state(last_movie_id)

                # Small delay to prevent overwhelming the databases
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in ETL process: {e}")
            raise
        finally:
            await self.es_client.close()
            if hasattr(self, "pg_pool"):
                await self.pg_pool.close()


async def main():
    """Entry point of the application."""
    try:
        settings = Settings()
        etl = MovieETL(settings)
        await etl.run()
    except ValidationError as e:
        logger.error(f"Configuration validation error: {e}")
    except Exception as e:
        logger.error(f"Application error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
