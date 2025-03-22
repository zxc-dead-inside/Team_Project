import aiohttp
import pytest_asyncio
from settings import test_settings

@pytest_asyncio.fixture
async def make_get_request(session):
    """Fixture to use managed session."""

    async def inner(url: str) -> aiohttp.ClientResponse:
        response = await session.get(f"http://{test_settings.service_url}{url}")
        return response

    return inner