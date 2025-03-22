import asyncio
import pytest

pytest_plugins = (
    "fixtures.redis_fixtures",
    "fixtures.app_auth_fixtures"
    
)

@pytest.fixture(scope="session", autouse=True)
def wait_for_services(es_client, redis_client):
    """Wait for all required services to be ready."""


    max_retries = 30
    retries = 0

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
