import asyncio
import pytest

pytest_plugins = (
    "fixtures.elasticsearch_fixtures","fixtures.redis_fixtures",
    "fixtures.app_fastapi_fixtures"
    
)

@pytest.fixture(scope="session", autouse=True)
def wait_for_services(es_client, redis_client):
    """Wait for all required services to be ready."""

    # Check Elasticsearch
    max_retries = 30
    retries = 0
    while retries < max_retries:
        try:
            if es_client.ping():
                break
        except Exception:
            retries += 1
            if retries == max_retries:
                pytest.fail("Elasticsearch is not available")
            asyncio.sleep(1)

    # Check Redis
    retries = 0
    while retries < max_retries:
        try:
            if redis_client.ping():
                break
        except Exception:
            retries += 1
            if retries == max_retries:
                pytest.fail("Redis is not available")
            asyncio.sleep(1)
