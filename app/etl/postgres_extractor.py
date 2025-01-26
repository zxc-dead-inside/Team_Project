from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import backoff
import psycopg2
from logger_setup import logger
from psycopg2.extras import DictCursor


class PostgresExtractor:
    def __init__(self, dsn: str):
        self.dsn = dsn

    @backoff.on_exception(
        backoff.expo, (psycopg2.Error, psycopg2.OperationalError), max_tries=5
    )
    def _get_connection(self):
        return psycopg2.connect(self.dsn, cursor_factory=DictCursor)

    def _count_total_movies(self) -> int:
        query = "SELECT COUNT(*) FROM content.film_work"
        with self._get_connection() as conn, conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchone()[0]

    def extract_movies(
        self, last_modified: str | None, batch_size: int
    ) -> tuple[list[dict[str, Any]], datetime | None, datetime | None]:
        """
        Extract movies modified after a specific timestamp.
        Returns: (movies, latest_person_modified, latest_genre_modified)
        """
        logger.info(f"Extracting movies modified after: {last_modified}")

        query = """
        WITH updated_ids AS (
            SELECT DISTINCT 
                fw.id,
                MAX(p.modified) as max_person_modified,
                MAX(g.modified) as max_genre_modified
            FROM content.film_work fw
            LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
            LEFT JOIN content.person p ON p.id = pfw.person_id
            LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
            LEFT JOIN content.genre g ON g.id = gfw.genre_id
            WHERE fw.modified > %s::timestamp 
            OR p.modified > %s::timestamp
            OR g.modified > %s::timestamp
            GROUP BY fw.id
        )
        SELECT
            fw.id,
            fw.title,
            fw.description,
            fw.rating,
            fw.type,
            fw.created,
            fw.modified,
            ui.max_person_modified,
            ui.max_genre_modified,
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'role', pfw.role,
                        'id', p.id,
                        'name', p.full_name
                    )
                ) FILTER (WHERE p.id IS NOT NULL),
                '[]'
            ) as persons,
            ARRAY_AGG(DISTINCT g.name) as genres
        FROM updated_ids ui
        JOIN content.film_work fw ON fw.id = ui.id
        LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
        LEFT JOIN content.person p ON p.id = pfw.person_id
        LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
        LEFT JOIN content.genre g ON g.id = gfw.genre_id
        GROUP BY fw.id, ui.max_person_modified, ui.max_genre_modified
        ORDER BY fw.modified
        LIMIT %s;
        """

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query, (last_modified, last_modified, last_modified, batch_size)
                )
                results = cur.fetchall()

                if results:
                    processed_results = []
                    latest_person_modified = None
                    latest_genre_modified = None

                    for row in results:
                        processed_row = dict(row)

                        # Track latest modifications
                        if row["max_person_modified"] and (
                            not latest_person_modified
                            or row["max_person_modified"] > latest_person_modified
                        ):
                            latest_person_modified = row["max_person_modified"]
                        if row["max_genre_modified"] and (
                            not latest_genre_modified
                            or row["max_genre_modified"] > latest_genre_modified
                        ):
                            latest_genre_modified = row["max_genre_modified"]

                        # Remove temporary fields
                        del processed_row["max_person_modified"]
                        del processed_row["max_genre_modified"]

                        # Process persons to extract specific roles
                        persons = processed_row["persons"]
                        processed_row["actors_names"] = [
                            p["name"] for p in persons if p["role"] == "actor"
                        ]
                        processed_row["writers_names"] = [
                            p["name"] for p in persons if p["role"] == "writer"
                        ]
                        processed_row["directors_names"] = [
                            p["name"] for p in persons if p["role"] == "director"
                        ]
                        processed_row["actors"] = [
                            {"id": p["id"], "name": p["name"]}
                            for p in persons
                            if p["role"] == "actor"
                        ]
                        processed_row["directors"] = [
                            {"id": p["id"], "name": p["name"]}
                            for p in persons
                            if p["role"] == "director"
                        ]

                        processed_row["writers"] = [
                            {"id": p["id"], "name": p["name"]}
                            for p in persons
                            if p["role"] == "writer"
                        ]


                        processed_results.append(processed_row)

                    logger.info(f"Found {len(processed_results)} movies to process")
                    return (
                        processed_results,
                        latest_person_modified,
                        latest_genre_modified,
                    )
                return [], None, None
