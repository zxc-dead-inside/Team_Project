from etl.database import DBClient
from etl.state import StateStorage
from core.logger import setup_logger

logger = setup_logger("extract")
BATCH_SIZE = 100


class Extractor:
    """я делал метод класса _extract который выступал в роли конструктора для SQL,
    но у меня возникли проблемы с передачей списка параметров в качестве аргумента
    поэтому я вернулся к сырым запросам"""

    def __init__(self, state_storage: StateStorage, db_client: DBClient):
        self.state_storage = state_storage
        self.db_client = db_client


    def extract_film_changes(self) -> list[dict]:
        last_synced_time = self.state_storage.get_last_synced_time()
        offset = 0
        while True:
            query = """
            SELECT id, modified
            FROM content.film_work
            WHERE modified > %s
            ORDER BY modified
            LIMIT %s OFFSET %s;
            """
            cursor = self.db_client.execute_query_cursor(query, (last_synced_time, BATCH_SIZE, offset))
            results = cursor.fetchall()
            if not results:
                break

            yield results

            offset += BATCH_SIZE


    def extract_person_changes(self) -> list[dict]:
        last_synced_time = self.state_storage.get_last_synced_time()
        offset = 0
        while True:
            query = """
            SELECT id, modified
            FROM content.person
            WHERE modified > %s
            ORDER BY modified
            LIMIT %s OFFSET %s;
            """
            cursor = self.db_client.execute_query_cursor(query, (last_synced_time, BATCH_SIZE, offset))
            results = cursor.fetchall()
            if not results:
                break

            yield results

            offset += BATCH_SIZE

    def extract_genre_changes(self) -> list[dict]:
        last_synced_time = self.state_storage.get_last_synced_time()
        offset = 0
        while True:
            query = """
            SELECT id, modified
            FROM content.genre
            WHERE modified > %s
            ORDER BY modified
            LIMIT %s OFFSET %s;
            """
            cursor = self.db_client.execute_query_cursor(query, (last_synced_time, BATCH_SIZE, offset))
            results = cursor.fetchall()
            if not results:
                break

            yield results

            offset += BATCH_SIZE

    def extract_films_for_people(self, people_ids: list[str]) -> list[dict]:
        offset = 0
        while True:
            query = """
            SELECT fw.id, fw.modified
            FROM content.film_work fw
            LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
            WHERE pfw.person_id IN %s
            ORDER BY fw.modified
            LIMIT %s OFFSET %s;
            """
            cursor = self.db_client.execute_query_cursor(query, (tuple(people_ids), BATCH_SIZE, offset))
            results = cursor.fetchall()

            if not results:
                break

            yield results

            offset += BATCH_SIZE

    def extract_films_for_genres(self, genre_ids: list[str]) -> list[dict]:
        offset = 0
        while True:
            query = """
            SELECT fw.id, fw.modified
            FROM content.film_work fw
            LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
            WHERE gfw.genre_id IN %s
            ORDER BY fw.modified
            LIMIT %s OFFSET %s;
            """
            cursor = self.db_client.execute_query_cursor(query, (tuple(genre_ids), BATCH_SIZE, offset))
            results = cursor.fetchall()

            if not results:
                break

            yield results

            offset += BATCH_SIZE

    def extract_full_film_data(self, film_ids: list[str]) -> list[dict]:
        query = """
        SELECT
            fw.id AS fw_id, 
            fw.title, 
            fw.description, 
            fw.rating, 
            fw.type, 
            fw.created, 
            fw.modified, 
            pfw.role, 
            p.id AS person_id, 
            p.full_name,
            g.name AS genre_name
        FROM content.film_work fw
        LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
        LEFT JOIN content.person p ON p.id = pfw.person_id
        LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
        LEFT JOIN content.genre g ON g.id = gfw.genre_id
        WHERE fw.id IN %s;
        """
        cursor = self.db_client.execute_query_cursor(query, (tuple(film_ids),))

        film_dict = {}
        while results := cursor.fetchall():
            for row in results:
                film_id = row['fw_id']

                if film_id not in film_dict:
                    film_dict[film_id] = {
                        "fw_id": row['fw_id'],
                        "title": row['title'],
                        "description": row['description'],
                        "rating": row['rating'],
                        "type": row['type'],
                        "created": row['created'],
                        "modified": row['modified'],
                        "actors": [],
                        "directors": [],
                        "writers": [],
                        "genres": []
                    }
                person = {
                    "id": row['person_id'],
                    "name": row['full_name']
                }
                if row['role'] == 'actor':
                    if person not in film_dict[film_id]['actors']:
                        film_dict[film_id]['actors'].append(person)
                elif row['role'] == 'director':
                    if person not in film_dict[film_id]['directors']:
                        film_dict[film_id]['directors'].append(person)
                elif row['role'] == 'writer':
                    if person not in film_dict[film_id]['writers']:
                        film_dict[film_id]['writers'].append(person)

                if row['genre_name'] and row['genre_name'] not in \
                        film_dict[film_id]['genres']:
                    film_dict[film_id]['genres'].append(row['genre_name'])

            films_transformed = list(film_dict.values())
            yield films_transformed
            film_dict.clear()
