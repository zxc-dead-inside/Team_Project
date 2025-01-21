from psycopg import connection as _connection
from psycopg.rows import dict_row

from backoff import backoff, check_connection
from queries import queries
from settings import DB_READ_LIMIT
from structs import data_structs
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

        changed_uuid = self.get_data(
            data_structs.base_dataset,
            queries.get_id_by_date(
                date, table_name, offset, limit))
        return changed_uuid

    def get_fw_by_id(self, ids, mtm_name, key_field):
        """Получает список film_work из списка id связанной
        таблицы."""

        offset = 0
        limit = DB_READ_LIMIT
        while True:
            film_work_uuid = self.get_data(
                data_structs.base_dataset,
                queries.get_film_ids_by_id(
                    mtm_name, key_field, ids, offset, limit))
            film_work_ids = get_uuid_list(film_work_uuid)

            if len(film_work_ids) == 0:
                break
            offset += limit
            yield film_work_ids
