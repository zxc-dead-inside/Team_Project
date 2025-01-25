from psycopg import connection as _connection
from psycopg.rows import dict_row

from backoff import backoff, check_connection
from queries import queries
from settings import DB_READ_LIMIT
from structs import BaseDataSet, GenreFilmWorks, PeopleFilmWorks
from utils import get_uuid_list


class PostgresLoader:
    """Класс для извлечения данных из базы PostgreSQL."""

    def __init__(self, pg_conn: _connection):
        self.cursor = pg_conn.cursor(row_factory=dict_row)
        self.pg_conn = pg_conn

    def __del__(self):
        self.pg_conn.close()

    @backoff()
    @check_connection()
    def extract_data(self, query: str):
        """Забирает данные из таблицы."""

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_data(self, struct, query):
        """Преобразовывает данные в dataclass."""

        batch = self.extract_data(query)
        yield [struct(**dict(data)) for data in batch]

    def get_changed_records(
            self, date, table_name, offset, limit):
        """Получает изменившиеся данные."""

        query = queries.get_id_by_date(
                date, table_name, offset, limit)
        changed_uuid = self.get_data(BaseDataSet, query)
        return changed_uuid

    def get_fw_by_id(self, ids, mtm_name, key_field):
        """Получает список film_work из списка id связанной
        таблицы."""

        offset = 0
        limit = DB_READ_LIMIT
        while True:
            query = queries.get_film_ids_by_id(
                mtm_name, key_field, ids, offset, limit)
            film_work_uuid = self.get_data(BaseDataSet, query)
            film_work_ids = get_uuid_list(film_work_uuid)

            if len(film_work_ids) == 0:
                break
            yield film_work_ids
            offset += limit

    def get_fw(self, ids, mtm):
        """
        Получает необходимую для изменения в es часть по film_work.
        """

        offset = 0
        limit = DB_READ_LIMIT

        if mtm == 'person':
            struct = PeopleFilmWorks

        elif mtm == 'genre':
            struct = GenreFilmWorks

        while True:
            if mtm == 'person':
                query = queries.get_people_fw(ids, offset, limit)

            elif mtm == 'genre':
                query = queries.get_genres_fw(ids, offset, limit)

            data = self.get_data(struct, query)
            data = [item for item in data]
            if not len(data[0]):
                break
            yield data
            offset += limit
