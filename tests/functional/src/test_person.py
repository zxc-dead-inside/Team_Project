import uuid
from http import HTTPStatus
from typing import Any

import pytest
import pytest_asyncio
from settings import test_settings


@pytest.fixture
def person_data() -> list[dict[str, Any]]:
    """Fixture providing test person data with associated films."""

    persons = [
        {
            "uuid": str(uuid.uuid4()),
            "full_name": "John Doe",
            "films": [{"id": str(uuid.uuid4()), "roles": ["actor", "director"]}],
        },
        {
            "uuid": str(uuid.uuid4()),
            "full_name": "Alice Smith",
            "films": [{"id": str(uuid.uuid4()), "roles": ["actor"]}],
        },
    ]

    return [
        {
            "_index": test_settings.person_index,
            "_id": person["uuid"],
            "_source": {
                "id": person["uuid"],
                "full_name": person["full_name"],
                "films": person["films"],
            },
        }
        for person in persons
    ]


@pytest.fixture
def film_data(person_data) -> list[dict[str, Any]]:
    """Fixture providing test film data linked to test persons."""
    films = []
    for person in person_data:
        for film in person["_source"]["films"]:
            films.append(
                {
                    "_index": test_settings.movie_index,
                    "_id": film["id"],
                    "_source": {
                        "id": film["id"],
                        "title": f"Test Movie for {person['_source']['full_name']}",
                        "imdb_rating": 8.5,
                    },
                }
            )
    return films


@pytest.mark.asyncio
class TestPersonAPI:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, es_write_data, person_data, film_data):
        """Setup test data"""
        await es_write_data(person_data)
        await es_write_data(film_data)

    async def test_persons_list(self, make_get_request):
        """Test default list endpoint."""
        response = await make_get_request(test_settings.person_endpoint)
        assert response.status == HTTPStatus.OK

        data = await response.json()
        assert len(data) == 2
        assert all(isinstance(person["uuid"], str) for person in data)
        assert all(isinstance(person["full_name"], str) for person in data)

    @pytest.mark.parametrize(
        "page_size,page_number,expected_count",
        [
            (10, 1, 2),  # default case
            (1, 1, 1),  # first page with size 1
            (1, 2, 1),  # second page with size 1
        ],
    )
    async def test_persons_list_pagination(
        self, make_get_request, page_size, page_number, expected_count
    ):
        response = await make_get_request(
            f"{test_settings.person_endpoint}?page_size={page_size}&page_number={page_number}"
        )
        assert response.status == HTTPStatus.OK

        data = await response.json()
        assert len(data) == expected_count

    async def test_persons_list_without_sort(self, make_get_request):
        """Test list endpoint without sort parameter."""
        response = await make_get_request(test_settings.person_endpoint)
        assert response.status == HTTPStatus.OK

        data = await response.json()
        assert len(data) > 0
        assert all(isinstance(person["uuid"], str) for person in data)
        assert all(isinstance(person["full_name"], str) for person in data)

    async def test_get_person_by_id(self, make_get_request, person_data):
        person_id = person_data[0]["_id"]
        response = await make_get_request(f"{test_settings.person_endpoint}{person_id}")
        assert response.status == HTTPStatus.OK

        data = await response.json()
        assert data["uuid"] == person_id
        assert data["full_name"] == person_data[0]["_source"]["full_name"]
        assert len(data["films"]) == len(person_data[0]["_source"]["films"])
        assert data["films"][0]["uuid"] == person_data[0]["_source"]["films"][0]["id"]
        assert (
            data["films"][0]["roles"] == person_data[0]["_source"]["films"][0]["roles"]
        )

    async def test_get_person_by_id_not_found(self, make_get_request):
        """Test getting a non-existent person."""
        non_existent_id = str(uuid.uuid4())
        response = await make_get_request(
            f"{test_settings.person_endpoint}{non_existent_id}"
        )
        assert response.status == HTTPStatus.NOT_FOUND

        # Test with invalid UUID format
        response = await make_get_request(
            f"{test_settings.person_endpoint}invalid-uuid"
        )
        assert response.status == HTTPStatus.NOT_FOUND

    async def test_get_films_by_person_id(
        self, make_get_request, person_data, film_data
    ):
        """Test getting films for a person."""
        person_id = person_data[0]["_id"]
        response = await make_get_request(
            f"{test_settings.person_endpoint}{person_id}/film"
        )
        assert response.status == HTTPStatus.OK

        data = await response.json()
        assert len(data) == 1

        # Use the film document _id for comparison.
        first_film = next(
            f
            for f in film_data
            if f["_id"] == person_data[0]["_source"]["films"][0]["id"]
        )
        assert data[0]["uuid"] == first_film["_id"]
        assert data[0]["title"] == first_film["_source"]["title"]
        assert data[0]["imdb_rating"] == first_film["_source"]["imdb_rating"]

    async def test_get_films_by_person_without_films(
        self, make_get_request, es_write_data
    ):
        """Test getting films for a person who has no films."""
        person_id = str(uuid.uuid4())
        person_without_films = {
            "_index": test_settings.person_index,
            "_id": person_id,
            "_source": {
                "id": person_id,
                "full_name": "No Films Person",
                "films": [],
            },
        }
        await es_write_data([person_without_films])

        response = await make_get_request(
            f"{test_settings.person_endpoint}{person_id}/film"
        )
        assert response.status == HTTPStatus.NOT_FOUND
