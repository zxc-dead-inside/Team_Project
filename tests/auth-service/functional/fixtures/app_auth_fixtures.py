import aiohttp
import pytest_asyncio
from settings import test_settings


@pytest_asyncio.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest_asyncio.fixture
async def make_post_request(session):
    """Fixture to use managed session."""

    async def inner(
            url: str,
            data: dict | None = None,
            headers: dict | None = None,
            params: dict | None = None
    ) -> aiohttp.ClientResponse:
        response = await session.post(
            url=f"http://{test_settings.service_url}{url}",
            json=data,
            headers=headers,
            params=params
        )
        return response

    return inner
