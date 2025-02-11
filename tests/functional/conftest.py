import asyncio

import pytest
import redis
from elasticsearch import Elasticsearch
from testdata.settings import test_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def es_client():
    """Create Elasticsearch client fixture."""
    client = Elasticsearch(
        hosts=test_settings.es_host,
        verify_certs=False,
        ssl_show_warn=False
    )
    
    # Ensure index exists with proper mapping
    if not client.indices.exists(index=test_settings.es_index):
        client.indices.create(
            index=test_settings.es_index,
            body=test_settings.es_index_mapping
        )
    
    yield client
    
    # Cleanup after tests
    client.indices.delete(index=test_settings.es_index, ignore=[404])


@pytest.fixture(scope="session")
def redis_client():
    """Create Redis client fixture."""
    client = redis.Redis(
        host=test_settings.redis_host,
        port=6379,
        decode_responses=True
    )
    
    yield client
    
    # Cleanup after tests
    client.flushdb()


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


@pytest.fixture
def clean_redis(redis_client):
    """Ensure Redis is clean before each test."""
    yield redis_client
    redis_client.flushdb()


@pytest.fixture
def clean_elasticsearch(es_client):
    """Ensure Elasticsearch is clean before each test."""
    yield es_client
    # Delete all documents but keep the index and mapping
    es_client.delete_by_query(
        index=test_settings.es_index,
        body={"query": {"match_all": {}}},
        refresh=True
    )
