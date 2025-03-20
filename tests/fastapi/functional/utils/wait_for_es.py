import backoff
from elasticsearch import Elasticsearch
from helpers import setup_logger
from settings import test_settings


logger = setup_logger(
    "elasticsearch_waiter"
)  # , 'logs/elasticsearch_wait.log'  Add log file if needed


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=10,
    on_backoff=lambda details: logger.warning(
        f"Attempt {details['tries']} failed. Retrying in {details['wait']:.1f} seconds..."
    ),
)
def check_elasticsearch_connection(client: Elasticsearch) -> bool:
    """
    Check Elasticsearch connection with exponential backoff.

    Args:
        client: Elasticsearch client instance

    Returns:
        bool: True if connection is successful

    Raises:
        Exception: If connection fails after max retries
    """
    if client.ping():
        return True
    raise Exception("Failed to connect to Elasticsearch")


if __name__ == "__main__":
    es_client = Elasticsearch(
        hosts=test_settings.es_url, verify_certs=False, ssl_show_warn=False
    )

    try:
        check_elasticsearch_connection(es_client)
        logger.info("Successfully connected to Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch after all retries: {e}")
        raise
