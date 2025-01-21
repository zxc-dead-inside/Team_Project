from datetime import datetime

from etl.database import DBClient
from etl.extract import Extractor
from etl.transform import transform_film_data
from etl.load import ElasticsearchClient
from etl.state import StateStorage
from etl.index import INDEX_ETL
from core.logger import setup_logger
from core.conf import config

logger = setup_logger("etl")

class ETLProcessor:
    def __init__(self, extractor: Extractor,
                 elasticsearch_client: ElasticsearchClient,
                 state_storage: StateStorage):
        self.extractor = extractor
        self.elasticsearch_client = elasticsearch_client
        self.state_storage = state_storage
        self.logger = setup_logger("ETLProcessor")

    def _transform_load(self, batch):
        transformed_data = transform_film_data(batch)
        self.elasticsearch_client.index_data(transformed_data)

    def run(self):
        self.logger.info("Запуск ETL процесса...")

        # Шаг 1: Обработка изменений для фильмов
        self.process_changes_for_films()

        # Шаг 2: Обработка изменений для актеров
        self.process_changes_for_persons()

        # Шаг 3: Обработка изменений для жанров
        self.process_changes_for_genres()

        # Обновление времени последней синхронизации
        last_synced_time = datetime.utcnow()
        self.state_storage.set_last_synced_time(last_synced_time)
        self.logger.info(
            f"Последнее время синхронизации обновлено на {last_synced_time}.")

    def process_changes_for_films(self):
        """Обработка изменений для фильмов."""
        self.logger.info("Обработка изменений для фильмов...")

        for changes_batch in self.extractor.extract_film_changes():
            if not changes_batch:
                self.logger.info("Нет изменений для фильмов.")
                break

            film_ids = [change['id'] for change in changes_batch]

            self.logger.info(
                f"Извлекаем и обрабатываем данные для {len(film_ids)} фильмов.")
            for related_batch in self.extractor.extract_full_film_data(
                    film_ids):
                self._transform_load(related_batch)

    def process_changes_for_persons(self):
        """Обработка изменений для актеров/персон."""
        self.logger.info("Обработка изменений для актеров...")

        for changes_batch in self.extractor.extract_person_changes():
            if not changes_batch:
                self.logger.info("Нет изменений для фильмов.")
                break

            person_ids = [change['id'] for change in changes_batch]

            for film_ids in self.extractor.extract_films_for_people(person_ids):
                film_ids = [film["id"] for film in film_ids]
                self.logger.info(
                    f"Извлекаем и обрабатываем данные для {len(film_ids)} фильмов.")
                for related_batch in self.extractor.extract_full_film_data(
                        film_ids):
                    self._transform_load(related_batch)

    def process_changes_for_genres(self):
        """Обработка изменений для жанров."""
        self.logger.info("Обработка изменений для жанров...")

        for changes_batch in self.extractor.extract_genre_changes():
            if not changes_batch:
                self.logger.info("Нет изменений для фильмов.")
                break

            genre_ids = [change['id'] for change in changes_batch]

            for film_ids in self.extractor.extract_films_for_genres(
                    genre_ids):
                film_ids = [film["id"] for film in film_ids]
                self.logger.info(
                    f"Извлекаем и обрабатываем данные для {len(film_ids)} фильмов.")
                for related_batch in self.extractor.extract_full_film_data(
                        film_ids):
                    self._transform_load(related_batch)


def etl_pipeline():
    # Инициализация
    state_storage = StateStorage("state.json")
    db_client = DBClient(host=config.sql_host, dbname=config.postgres_db,
                         user=config.postgres_user, password=config.postgres_password,)
    extractor = Extractor(state_storage, db_client)
    elasticsearch_client = ElasticsearchClient(
        es_host=f"http://{config.elasticsearch_host}:{config.elasticsearch_port}",
        index=config.elasticsearch_index,
        index_body=INDEX_ETL
    )

    etl_processor = ETLProcessor(extractor, elasticsearch_client,
                                 state_storage)

    # Запуск ETL процесса
    etl_processor.run()
