import asyncio
from typing import Any

import aiohttp
import pytest
import pytest_asyncio
import redis
from elasticsearch import AsyncElasticsearch, Elasticsearch
from elasticsearch.helpers import async_bulk
from settings import test_settings


@pytest_asyncio.fixture
async def make_get_request():
    async def inner(url: str) -> aiohttp.ClientResponse:
        session = aiohttp.ClientSession()
        try:
            response = await session.get(f"http://{test_settings.service_url}{url}")
            return response
        except Exception as e:
            await session.close()
            raise e

    return inner


@pytest_asyncio.fixture
async def es_write_data():
    """Generic fixture to write data to Elasticsearch."""

    async def inner(data: list[dict[str, Any]]):
        es_client = AsyncElasticsearch(hosts=test_settings.es_url, verify_certs=False)

        try:
            success, errors = await async_bulk(
                client=es_client, actions=data, refresh=True
            )

            if errors:
                raise Exception(f"Error writing data to Elasticsearch: {errors}")

        finally:
            await es_client.close()

    return inner


@pytest.fixture(scope="session")
def es_client():
    """Create Elasticsearch client fixture."""
    client = Elasticsearch(
        hosts=test_settings.es_url, verify_certs=False, ssl_show_warn=False
    )

    yield client

    # Cleanup after tests
    indices_to_clean = [
        test_settings.genre_index,
        # Add other indices as they are added to TestSettings
    ]

    for index in indices_to_clean:
        client.options(ignore_status=[404]).indices.delete(index=index)


@pytest.fixture(scope="session")
def redis_client():
    """Create Redis client fixture."""
    client = redis.Redis(
        host=test_settings.redis_host, port=6379, decode_responses=True
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
        index=test_settings.es_index, body={"query": {"match_all": {}}}, refresh=True
    )
