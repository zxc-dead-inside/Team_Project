import psycopg2
import psycopg2.extras
import backoff


class DBClient:
    def __init__(self, host: str, dbname: str, user: str, password: str):
        self.connection_params = {
            "host": host,
            "dbname": dbname,
            "user": user,
            "password": password,
        }
        self.conn = None
        self.cursor = None

    @backoff.on_exception(
        backoff.expo,
        psycopg2.OperationalError,
        max_time=60
    )
    def connect(self):
        """Устанавливает соединение с PostgreSQL с повторными попытками."""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def execute_query(self, query: str, params: tuple) -> list[dict]:
        if not self.conn or self.conn.closed:
            self.connect()
        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения запроса: {e}")

    def execute_query_cursor(self, query: str, params: tuple):
        if not self.conn or self.conn.closed:
            self.connect()
        try:

            self.cursor.execute(query, params)
            return self.cursor
        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения запроса с курсором: {e}")
