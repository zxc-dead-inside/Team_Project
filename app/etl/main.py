import time
from collections.abc import Generator
from datetime import UTC, datetime

from config import Settings
from elasticsearch_loader import ElasticsearchLoader
from logger_setup import logger
from postgres_extractor import PostgresExtractor

from state import JsonFileStorage, State


def get_latest_modified_timestamp(
    objects_modified=None,
    filmworks_modified=None,
    persons_modified=None,
    genres_modified=None
) -> datetime | None:
    """
    Get the latest modification timestamp across all entity types.
    """

    timestamps = []

    # Add objects modifications
    if objects_modified:
        timestamps.extend(
            object["modified"] for object in objects_modified
        )

    # Add filmwork modifications if available
    if filmworks_modified:
        timestamps.append(filmworks_modified)

    # Add person modifications if available
    if persons_modified:
        timestamps.append(persons_modified)

    # Add genre modifications if available
    if genres_modified:
        timestamps.append(genres_modified)

    return max(timestamps) if timestamps else None


def transfer_movies(
        postgres_extractor: PostgresExtractor,
        last_modified: str,
        settings: Settings,
        state: State,
        offset: int
) -> Generator[list, None, None]:
    """
    Extract movies and their related modifications from PostgreSQL
    """

    modified = last_modified
    while True:
        movies, persons_modified, genres_modified = (
            postgres_extractor.extract_movies(
                last_modified, settings.BATCH_SIZE, offset)
        )

        if not movies:
            stats = state.get_statistics('movies')
            logger.info(f"Current ETL Statistics: {stats}")
            state.set_state("offset", 0, 'movies')
            state.set_state("last_modified", modified, 'movies')
            return None
        logger.info(f"Found {len(movies)} movies to process")
        yield movies
        latest_modified = get_latest_modified_timestamp(
            movies, persons_modified, genres_modified)
        if latest_modified is not None:
            if latest_modified.isoformat() > modified:
                modified = latest_modified.isoformat()
        offset += settings.BATCH_SIZE
        state.set_state("offset", offset, 'movies')
        stats = state.get_statistics('movies')


def transfer_objects(
        postgres_extractor: PostgresExtractor,
        last_modified: str,
        settings: Settings,
        state: State,
        offset: int,
        index: str
) -> Generator[list, None, None]:
    """
    Extract objects and their related modifications from PostgreSQL
    """
    objects_modified, filmworks_modified, persons_modified, genres_modified = \
        None, None, None, None
    modified = last_modified

    while True:
        if index == 'movies':
            objects_modified, persons_modified, genres_modified = (
                postgres_extractor.extract_movies(
                    last_modified, settings.BATCH_SIZE, offset)
            )
        elif index == 'persons':
            objects_modified, filmworks_modified = (
                postgres_extractor.extract_persons(
                    last_modified, settings.BATCH_SIZE, offset)
            )

        if not objects_modified:
            stats = state.get_statistics(index)
            logger.info(f"Current ETL Statistics: {stats}")
            state.set_state("offset", 0, index)
            state.set_state("last_modified", modified, index)
            return None
        logger.info(f"Found {len(objects_modified)} {index} to process")
        yield objects_modified

        latest_modified = get_latest_modified_timestamp(
            objects_modified,
            filmworks_modified,
            persons_modified,
            genres_modified
        )

        if latest_modified is not None:
            if latest_modified.isoformat() > modified:
                modified = latest_modified.isoformat()
        offset += settings.BATCH_SIZE
        state.set_state("offset", offset, index)
        stats = state.get_statistics(index)


def main():
    # Load configuration
    settings = Settings()

    # Initialize components
    storage = JsonFileStorage(settings.STATE_FILE_PATH)
    state = State(storage)
    postgres_extractor = PostgresExtractor(settings.postgres_dsn)
    es_loader = ElasticsearchLoader(
        settings.ELASTICSEARCH_HOST, settings.ELASTICSEARCH_PORT
    )

    while True:
        try:
            for index in settings.INDECIES:
                last_modified = state.get_state(
                    "last_modified", index) or settings.BASE_DATE

                state.set_state(
                    "processing_started_at",
                    datetime.now(UTC).isoformat(), index)

                if index == 'movies':
                    logger.info(f" Starting {index} ETL")
                    logger.info(
                        f"Current state timestamp: {last_modified}")
                    offset = state.get_state("offset", index) or 0

                    movies = transfer_movies(
                        postgres_extractor, last_modified, settings,
                        state, offset
                    )

                    if movies is None:
                        continue

                    try:
                        # Load movies to Elasticsearch
                        es_loader.load_movies(movies)
                        state.set_state("offset", 0, index)
                    except Exception as e:
                        logger.error(f"Failed to process batch: {e}",
                                     exc_info=True)
                        stats = state.get_statistics(index)
                        logger.error(
                            f"Batch processing failed. Total failed: "
                            f"{stats['total_failed']}"
                        )
                        raise
                    stats = state.get_statistics(index)
                    logger.info(f"Current {index} ETL Statistics: {stats}")

                elif index == "genres":

                    logger.info(f" Starting {index} ETL")

                    genres = postgres_extractor.extract_genres(last_modified)

                    if not genres:
                        continue

                    latest_modified = max(
                        [genre[-1] for genre in genres])
                    logger.info(f"{latest_modified.isoformat()}")

                    try:
                        es_loader.load_genres(genres)
                    except Exception as e:
                        logger.error(
                            f"Failed to process batch: {e}",
                            exc_info=True)
                        stats = state.get_statistics(index)
                        logger.error(
                            "Batch processing failed. Total failed: "
                            f"{stats['total_failed']}"
                        )
                        raise

                    stats = state.get_statistics(index)
                    logger.info(f"Current {index} ETL Statistics: {stats}")

                    if latest_modified.isoformat() > last_modified:
                        state.set_state(
                            "last_modified",
                            latest_modified.isoformat(), index)

                elif index == "persons":
                    logger.info(f" Starting {index} ETL")
                    logger.info(
                        f"Current state timestamp: {last_modified}")
                    offset = state.get_state("offset", index) or 0

                    persons = transfer_objects(
                        postgres_extractor, last_modified, settings,
                        state, offset, index
                    )
                    if persons is None:
                        continue

                    try:
                        # Load movies to Elasticsearch
                        es_loader.load_persons(persons)
                        state.set_state("offset", 0, index)
                    except Exception as e:
                        logger.error(f"Failed to process batch: {e}",
                                     exc_info=True)
                        stats = state.get_statistics(index)
                        logger.error(
                            f"Batch processing failed. Total failed: "
                            f"{stats['total_failed']}"
                        )
                        raise
                    stats = state.get_statistics(index)
                    logger.info(f"Current {index} ETL Statistics: {stats}")

            logger.info("No new ETL to process. Sleeping...")
            time.sleep(settings.SLEEP_TIME)

        except Exception as e:
            logger.error(
                f"Error during ETL process: {e}", exc_info=True)
            time.sleep(settings.SLEEP_TIME)


if __name__ == "__main__":
    main()
