import time
from datetime import UTC, datetime

from config import Settings
from elasticsearch_loader import ElasticsearchLoader
from logger_setup import logger
from postgres_extractor import PostgresExtractor

from state import JsonFileStorage, State


def get_latest_modified_timestamp(
    movies, persons_modified, genres_modified
) -> datetime | None:
    """Get the latest modification timestamp across all entity types."""
    timestamps = []

    # Add movie modifications
    if movies:
        timestamps.extend(movie["modified"] for movie in movies)

    # Add person modifications if available
    if persons_modified:
        timestamps.append(persons_modified)

    # Add genre modifications if available
    if genres_modified:
        timestamps.append(genres_modified)

    return max(timestamps) if timestamps else None


def main():
    # Load configuration
    settings = Settings()

    # Initialize components
    storage = JsonFileStorage(settings.STATE_FILE_PATH)
    state = State(storage)
    postgres_extractor = PostgresExtractor(str(settings.postgres_dsn))
    es_loader = ElasticsearchLoader(
        settings.ELASTICSEARCH_HOST, settings.ELASTICSEARCH_PORT
    )

    # Set processing start time if not already set
    if not state.get_state("processing_started_at"):
        state.set_state("processing_started_at", datetime.now(UTC).isoformat())

    # Log initial statistics
    stats = state.get_statistics()
    logger.info(f"ETL Process Statistics: {stats}")

    while True:
        try:
            last_modified = state.get_state("last_modified") or "1970-01-01T00:00:00"
            logger.info(f"Current state timestamp: {last_modified}")

            # Extract movies and their related modifications from PostgreSQL
            movies, persons_modified, genres_modified = (
                postgres_extractor.extract_movies(last_modified, settings.BATCH_SIZE)
            )

            if not movies:
                logger.info("No new movies to process. Sleeping...")
                stats = state.get_statistics()
                logger.info(f"Current ETL Statistics: {stats}")
                time.sleep(settings.SLEEP_TIME)
                continue

            logger.info(f"Found {len(movies)} movies to process")

            try:
                # Load movies to Elasticsearch
                es_loader.load_movies(movies)

                state.increment_processed(len(movies))

                # Calculate and update the latest modification timestamp
                latest_modified = get_latest_modified_timestamp(
                    movies, persons_modified, genres_modified
                )

                if latest_modified:
                    new_timestamp = latest_modified.isoformat()
                    if new_timestamp > last_modified:
                        state.set_state("last_modified", new_timestamp)
                        logger.info(
                            f"Updated last_modified timestamp to: {new_timestamp}"
                        )

                # Log success with updated statistics
                stats = state.get_statistics()
                logger.info(
                    f"Successfully processed {len(movies)} movies. "
                    f"Total processed: {stats['total_processed']}"
                )

            except Exception as e:
                state.increment_failed(len(movies))
                logger.error(f"Failed to process batch: {e}", exc_info=True)
                stats = state.get_statistics()
                logger.error(
                    f"Batch processing failed. Total failed: {stats['total_failed']}"
                )
                raise

        except Exception as e:
            logger.error(f"Error during ETL process: {e}", exc_info=True)
            time.sleep(settings.SLEEP_TIME)


if __name__ == "__main__":
    main()
