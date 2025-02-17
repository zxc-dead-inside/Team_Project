from typing import Any, AsyncGenerator

import aiohttp
import pytest
import pytest_asyncio

from elasticsearch import AsyncElasticsearch, Elasticsearch
from elasticsearch.helpers import async_bulk

from settings import test_settings

@pytest_asyncio.fixture
async def session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Fixture to manage aiohttp client session."""

    session = aiohttp.ClientSession()
    yield session
    await session.close()

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


@pytest_asyncio.fixture
async def create_index_factory():
    """Fixture factory for creating Elasticsearch indices with specified mappings."""

    async def create_index(
        index_name: str, mapping: dict[str, Any], *, recreate: bool = False
    ) -> None:
        """
        Create an Elasticsearch index with the specified mapping.

        Args:
            index_name: Name of the index to create
            mapping: Index mapping configuration
            recreate: If True, delete existing index before creation
        """
        async with AsyncElasticsearch(
            hosts=test_settings.es_url, verify_certs=False
        ) as es_client:
            exists = await es_client.indices.exists(index=index_name)

            if exists and recreate:
                await es_client.indices.delete(index=index_name)
                exists = False

            if not exists:
                # Using unpacked mapping instead of deprecated 'body' parameter
                await es_client.indices.create(
                    index=index_name,
                    mappings=mapping.get("mappings", {}),
                    settings=mapping.get("settings", {}),
                )

    return create_index


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
        test_settings.movie_index,
    ]

    for index in indices_to_clean:
        client.options(ignore_status=[404]).indices.delete(index=index)

@pytest.fixture
def clean_elasticsearch(es_client):
    """Ensure Elasticsearch is clean before each test."""

    yield es_client
    # Delete all documents but keep the index and mapping
    es_client.delete_by_query(
        index=test_settings.es_index, body={"query": {"match_all": {}}}, refresh=True
    )

@pytest_asyncio.fixture(name="es_create_index")
def es_create_index():
    async def inner(
            index: str, settings: dict[str, Any], mappings: dict[str, Any]
    ):
        """Generic fixture to create an elasticsearch index."""

        es_client = AsyncElasticsearch(
            hosts=test_settings.es_url, verify_certs=False)
        try:
            if await es_client.indices.exists(index=index):
                await es_client.indices.delete(index=index)
            await es_client.indices.create(
                index=index, settings=settings, mappings=mappings
            )
        except Exception as e:
            raise (f"Index creation error: {e}")
        finally:
            await es_client.close()
    return inner