import pytest
import redis

from settings import test_settings


@pytest.fixture(scope="session")
def redis_client():
    """Create Redis client fixture."""

    client = redis.Redis.from_url(test_settings.redis_url)
    # client = redis.Redis(
    #     host=test_settings.redis_host, port=6379, decode_responses=True
    # )

    yield client

    # Cleanup after tests
    client.flushdb()


@pytest.fixture
def clean_redis(redis_client):
    """Ensure Redis is clean before each test."""

    yield redis_client
    redis_client.flushdb()
