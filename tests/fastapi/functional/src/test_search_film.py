import uuid
from http import HTTPStatus
from typing import Any

import pytest
import pytest_asyncio
from testdata.es_mapping import es_indices_settings
from settings import test_settings

def movie_data() -> list[dict[str, Any]]:
    """Fixture providing test movie data for searching purpose."""

    film_id = str(uuid.uuid4())
    return {
        'id': film_id,
        'imdb_rating': 8.5,
        'title': 'The Star',
        'description': 'New World',
        'actors_names': ['Ann', 'Bob'],
        'writers_names': ['Ben', 'Howard'],
        'directors_names': ['Ken', 'Barby'],
        'genres': [
            {'id': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f96','name': 'Action'},
            {'id': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f97','name': 'Sci-Fi'}
        ],
        'actors': [
            {'id': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95', 'name': 'Ann'},
            {'id': 'fb111f22-121e-44a7-b78f-b19191810fbf', 'name': 'Bob'}
        ],
        'writers': [
            {'id': 'caf76c67-c0fe-477e-8766-3ab3ff2574b5', 'name': 'Ben'},
            {'id': 'b45bd7bc-2e16-46d5-b125-983d356768c6', 'name': 'Howard'}
        ],
        'directors': [
            {'id': 'caf86c67-c0fe-477e-8766-3ab3ff2574b5', 'name': 'Ken'},
            {'id': 'b45bd8bc-2e16-46d5-b125-983d356768c6', 'name': 'Barby'}
        ],
    }

class TestFilmSearchAPI:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, es_create_index, es_write_data):
        """Setup test data."""

        await es_create_index(
            test_settings.movie_index,
            es_indices_settings.movies_settings,
            es_indices_settings.movies_mappings
        )
        
        es_data = [movie_data() for _ in range(60)]
        bulk_query: list[dict] = []
        for row in es_data:
            data = {'_index': 'movies', '_id': row['id']}
            data.update({'_source': row})
            bulk_query.append(data)

        await es_write_data(bulk_query)


    @pytest.mark.parametrize(
        'query_data, expected_answer',
        [(
                    {'search': 'The Star'},
                    {
                        'status': HTTPStatus.OK,
                        'length': test_settings.film_count
                    }
            ),
            (
                    {'search': 'Mashed potato'},
                    {
                        'status': HTTPStatus.NOT_FOUND,
                        'length': test_settings.film_not_found_len
                    }
            )
        ]
    )
    @pytest.mark.asyncio
    async def test_film_search(
        self, make_get_request, query_data, expected_answer):
        """Test searching films."""
        
        url = test_settings.film_search_endpoint.substitute(
            search=query_data['search'])

        response = await make_get_request(url)
        body = await response.json()

        assert response.status == expected_answer['status']
        assert len(body) == expected_answer['length']