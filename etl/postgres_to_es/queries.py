"""
Функции возвращают готовые SQL запросы к базе данных.
"""
import datetime as dt
from typing import Tuple
from uuid import UUID


class Queries:

    def get_id_by_date(
            self, date: dt.datetime, table_name: str,
            offset: int = 0, limit: int = 100) -> str:
        """
        Запрос на список id, у которых изменились записи после
        определеной даты.
        """

        return (
            f"""\
            SELECT
                id,
                updated_at
            FROM content.{table_name}
            WHERE updated_at > '{date}'
            ORDER BY updated_at
            OFFSET {offset}
            LIMIT {limit};
            """)

    def get_film_ids_by_id(
            self,
            table_name: str,
            key_field: str,
            uuids: Tuple[UUID],
            offset: int = 0,
            limit: int = 100) -> str:
        """
        Запрос на список фильмов по id фильмов по id из left join.
        """

        return (
            f"""\
            SELECT
                DISTINCT(fw.id),
                fw.updated_at
            FROM content.film_work fw
            LEFT JOIN content.{table_name} tb ON tb.film_work_id = fw.id
            WHERE tb.{key_field} IN {uuids}
            ORDER BY fw.updated_at
            OFFSET {offset}
            LIMIT {limit};""")

    def get_people_fw(
            self, fids: Tuple[UUID], offset: int, limit: int):
        """Запрос на получение людей связанных с фильмом."""

        return (
            f"""\
            SELECT
                fw.id,
                fw.updated_at,
            COALESCE (
                json_agg(
                    DISTINCT jsonb_build_object(
                        'id',
                        p.id,
                        'name',
                        p.full_name
                    )
                ) FILTER (
                    WHERE p.id is not null and pfw.role = 'actor'
                ),
                '[]')
            as actors,
            COALESCE (
                json_agg(
                    DISTINCT jsonb_build_object(
                        'id',
                        p.id,
                        'name',
                        p.full_name
                    )
                ) FILTER (
                    WHERE p.id is not null and pfw.role = 'writer'
                ), '[]') as writers,
            COALESCE (
                json_agg(
                    DISTINCT jsonb_build_object(
                        'id',
                        p.id,
                        'name',
                        p.full_name
                    )
                ) FILTER (
                    WHERE p.id is not null and pfw.role = 'director'),
                    '[]') as directors
            FROM content.film_work fw
            LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
            LEFT JOIN content.person p ON p.id = pfw.person_id
            WHERE fw.id in {fids}
            GROUP BY fw.id
            LIMIT {limit}
            OFFSET {offset};""")

    def get_genres_fw(
            self, fids: Tuple[UUID], offset: int, limit: int):
        """Запрос на получение жанров связанных с фильмом."""

        return (
            f"""\
            SELECT
                fw.id,
                fw.updated_at,
                array_agg(DISTINCT g.name) as genres
            FROM content.film_work fw
            LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
            LEFT JOIN content.genre g ON g.id = gfw.genre_id
            WHERE fw.id in {fids}
            GROUP BY fw.id
            LIMIT {limit}
            OFFSET {offset};""")

    def get_changed_fw(
            self, date, offset: int, limit: int):
        """Возвращает список обновленных фильмов и шоу."""

        return (
            f"""\
            SELECT
                fw.id,
                fw.title,
                fw.description,
                fw.rating,
                fw.type,
                fw.updated_at
            FROM content.film_work fw
            WHERE  fw.updated_at > '{date}'
            ORDER BY fw.updated_at
            OFFSET {offset}
            LIMIT {limit};""")

    def etl_init(self, offset: int = 0, limit: int = 100):
        """
        Запрос для первоначальной загрузки данных es.
        """

        return (
            f"""\
            SELECT
                fw.id,
                fw.title,
                fw.description,
                fw.rating,
                fw.type,
                fw.created_at,
                fw.updated_at,
                COALESCE (
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'id', p.id,
                            'name', p.full_name
                        )
                    ) FILTER (
                        WHERE p.id is not null and pfw.role = 'actor'),
                        '[]') as actors,
                COALESCE (
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'id', p.id,
                            'name', p.full_name
                        )
                    ) FILTER (
                        WHERE p.id is not null and pfw.role = 'writer'),
                        '[]') as writers,
                COALESCE (
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'id', p.id,
                            'name', p.full_name
                        )
                    ) FILTER (
                        WHERE p.id is not null and pfw.role = 'director'),
                        '[]') as directors,
                array_agg(DISTINCT g.name) as genres
            FROM content.film_work fw
            LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
            LEFT JOIN content.person p ON p.id = pfw.person_id
            LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
            LEFT JOIN content.genre g ON g.id = gfw.genre_id
            GROUP BY fw.id
            LIMIT {limit}
            OFFSET {offset};""")


queries = Queries()
