import uuid
from http import HTTPStatus
from typing import Any, Callable

import pytest
import pytest_asyncio
from settings import test_settings
from testdata.es_mapping import GENRE_MAPPING


@pytest_asyncio.fixture
async def create_genre_index(create_index_factory: Callable):
    """Fixture to create genres index."""
    async def inner():
        await create_index_factory(
            test_settings.genre_index,
            GENRE_MAPPING,
            recreate=True
        )
    return inner


@pytest.fixture
def genre_data() -> list[dict[str, Any]]:
    """Fixture providing test genre data with predictable sorting order."""
    genres = [
        {"id": str(uuid.uuid4()), "name": "Action", "description": "Action movies"},
        {"id": str(uuid.uuid4()), "name": "Comedy", "description": "Comedy movies"},
        {"id": str(uuid.uuid4()), "name": "Drama", "description": "Drama movies"},
    ]

    return [
        {
            "_index": test_settings.genre_index,
            "_id": str(genre["id"]),
            "_source": {"id": genre["id"], "name": genre["name"]},
        }
        for genre in genres
    ]


@pytest.mark.asyncio
class TestGenreList:
    """Test suite for genre listing endpoints."""
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, es_write_data, genre_data, create_genre_index):
        """Setup test data"""
        await create_genre_index()
        await es_write_data(genre_data)

    async def test_get_genre_list(
        self, make_get_request, genre_data
    ) -> None:
        """Test getting list of genres with default parameters."""

        response = await make_get_request(test_settings.genre_endpoint)

        assert response.status == HTTPStatus.OK
        data = await response.json()

        assert len(data) == min(len(genre_data), 10)
        for item in data:
            assert "uuid" in item
            assert "name" in item
            assert isinstance(item["uuid"], str)
            assert isinstance(item["name"], str)

    async def test_get_genre_list_pagination(
        self, make_get_request
    ) -> None:
        """Test genre list pagination functionality."""

        # Test with specific page size
        response = await make_get_request(f"{test_settings.genre_endpoint}?page_size=2")
        assert response.status == HTTPStatus.OK
        data = await response.json()
        assert len(data) == 2

        # Test with page number
        response = await make_get_request(f"{test_settings.genre_endpoint}?page_number=2&page_size=1")
        assert response.status == HTTPStatus.OK
        data = await response.json()
        assert len(data) == 1

    async def test_get_genre_list_invalid_pagination(
        self, make_get_request
    ) -> None:
        """Test genre list with invalid pagination parameters."""
        # await es_write_data(genre_data)

        # Test invalid page size
        response = await make_get_request(f"{test_settings.genre_endpoint}?page_size=0")
        assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY

        # Test page size exceeding maximum
        response = await make_get_request(f"{test_settings.genre_endpoint}?page_size=101")
        assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY

        # Test invalid page number
        response = await make_get_request(f"{test_settings.genre_endpoint}?page_number=0")
        assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY

    async def test_get_genre_list_sorting(
        self, make_get_request
    ) -> None:
        """Test genre list sorting functionality."""
        # await es_write_data(genre_data)

        # First ensure data is loaded
        response = await make_get_request(test_settings.genre_endpoint)
        assert response.status == HTTPStatus.OK
        initial_data = await response.json()
        assert len(initial_data) > 0

        # Test sorting by name ascending
        response = await make_get_request(f"{test_settings.genre_endpoint}?sort=name")
        assert response.status == HTTPStatus.OK
        data = await response.json()
        names = [item["name"] for item in data]
        assert names == sorted(names)

        # Test sorting by name descending
        response = await make_get_request(f"{test_settings.genre_endpoint}?sort=-name")
        assert response.status == HTTPStatus.OK
        data = await response.json()
        names = [item["name"] for item in data]
        assert names == sorted(names, reverse=True)

    async def test_get_genre_list_invalid_sorting(
        self, make_get_request
    ) -> None:
        """Test genre list with empty sorting parameters."""
        # await es_write_data(genre_data)

        # Test with empty sort parameter
        response = await make_get_request(f"{test_settings.genre_endpoint}?sort=")
        assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
class TestGenreDetail:
    """Test suite for genre detail endpoint."""

    async def test_get_genre_by_id(
        self, es_write_data, genre_data, make_get_request
    ) -> None:
        """Test successfully retrieving a genre by ID."""
        await es_write_data(genre_data)

        # Get the ID from the first genre in test data
        genre_id = genre_data[0]["_id"]

        response = await make_get_request(f"{test_settings.genre_endpoint}{genre_id}")

        assert response.status == HTTPStatus.OK
        data = await response.json()

        assert isinstance(data, dict)
        assert "uuid" in data
        assert "name" in data
        assert data["uuid"] == genre_id
        assert isinstance(data["name"], str)

    async def test_get_genre_not_found(
        self, es_write_data, genre_data, make_get_request
    ) -> None:
        """Test response when genre ID doesn't exist."""
        await es_write_data(genre_data)

        non_existent_id = str(uuid.uuid4())
        response = await make_get_request(f"{test_settings.genre_endpoint}{non_existent_id}")

        assert response.status == HTTPStatus.NOT_FOUND
        data = await response.json()
        assert "detail" in data
        assert data["detail"] == "Genre not found"

    async def test_get_genre_invalid_id(self, make_get_request) -> None:
        """Test response when genre ID is invalid UUID."""
        invalid_id = "not-a-uuid"
        response = await make_get_request(f"{test_settings.genre_endpoint}{invalid_id}")

        assert response.status == HTTPStatus.NOT_FOUND
        data = await response.json()
        assert "detail" in data
        assert data["detail"] == "Genre not found"
