import backoff
import redis
from helpers import setup_logger
from settings import test_settings


logger = setup_logger("redis_waiter")  # , 'logs/redis_wait.log' Add log file if needed


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=10,
    on_backoff=lambda details: logger.warning(
        f"Attempt {details['tries']} failed. Retrying in {details['wait']:.1f} seconds..."
    ),
)
def check_redis_connection(client: redis.Redis) -> bool:
    """
    Check Redis connection with exponential backoff.

    Args:
        client: Redis client instance

    Returns:
        bool: True if connection is successful

    Raises:
        Exception: If connection fails after max retries
    """

    if client.ping():
        return True
    raise Exception("Failed to connect to Redis")


if __name__ == "__main__":
    redis_client = redis.from_url(test_settings.redis_url)
    # redis_client = redis.Redis(
    #     host=test_settings.redis_host,
    #     port=test_settings.redis_port,
    #     password=test_settings.redis_password,
    #     decode_responses=True,
    # )
    logger.info(f"redis_host: {test_settings.redis_host}")
    logger.info(f"redis_port: {test_settings.redis_port}")
    logger.info(f"redis_password: {test_settings.redis_password}")
    logger.info(f"redis_url: {test_settings.redis_url}")

    try:
        check_redis_connection(redis_client)
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis after all retries: {e}")
        raise
