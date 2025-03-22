import aiohttp
import json
import pytest_asyncio
from typing import AsyncGenerator
from settings import test_settings

@pytest_asyncio.fixture
async def session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Fixture to manage aiohttp client session."""

    session = aiohttp.ClientSession()
    yield session
    await session.close()

@pytest_asyncio.fixture
async def make_get_request(session: aiohttp.ClientSession):
    """Fixture to use managed session."""
    
    async def inner(
            url: str,
            headers: dict = None,
            data: dict = None,
            json: json = None,
            timeout: int = 30
    ) -> aiohttp.ClientResponse:
        response = await session.get(
            f'http://{test_settings.service_url}{url}',
            headers=headers,
            data=data,
            json=json,
            timeout=aiohttp.ClientTimeout(timeout)
        )
        return response

    return inner

@pytest_asyncio.fixture
async def make_post_request(session: aiohttp.ClientSession):
    """Fixture to use managed session."""
    
    async def inner(
            url: str,
            headers: dict = None,
            data: dict = None,
            json: json = None,
            timeout: int = 5
    ) -> aiohttp.ClientResponse:
        response = await session.post(
            f'http://{test_settings.service_url}{url}',
            headers=headers,
            data=data,
            json=json,
            timeout=aiohttp.ClientTimeout(timeout)
        )
        return response

    return inner