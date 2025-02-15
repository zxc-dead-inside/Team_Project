import uuid
from http import HTTPStatus
from random import choice
from typing import Any

import pytest
import pytest_asyncio
from testdata.es_mapping import es_indecies
from settings import test_settings

def person_data() -> list[dict[str, Any]]:
    """Fixture providing test movie data for searching purpose."""

    film_id = str(uuid.uuid4())
    person_id = str(uuid.uuid4())
    first_names = ['Bob', 'Anne', 'Alice', 'Jhon']
    second_names = ['Wick', 'Marley', 'Cooper', 'Hathaway']

    return {
        {
                "id": person_id,
                "full_name": "Anne Hathaway",
                "films": [{"id": film_id, "roles": ["actor"]}],
        },
    }

class TestPersonSearchhAPI:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, es_create_index, es_write_data):
        """Setup test data."""

        await es_create_index(
            test_settings.person_index,
            es_indecies.persons_index_settings,
            es_indecies.persons_mappings
        )
        
        es_data = [person_data() for _ in range(60)]
        
        bulk_query: list[dict] = []
        for row in es_data:
            data = {'_index': 'persons', '_id': row['id']}
            data.update({'_source': row})
            bulk_query.append(data)
        await es_write_data(bulk_query)


    @pytest.mark.parametrize(
        'query_data, expected_answer',
        [(
                    {'search': 'Anne'},
                    {
                        'status': HTTPStatus.OK,
                        'length': test_settings.person_count
                    }
            ),
            (
                    {'search': 'Sailor Moon'},
                    {
                        'status': HTTPStatus.NOT_FOUND,
                        'length': test_settings.person_not_found_len
                    }
            )
        ]
    )
    @pytest.mark.asyncio
    async def test_person_search(
        self, make_get_request, query_data, expected_answer):
        url = (
            f'/api/v1/persons/search?query={query_data["search"]}'
            '&page_number=1&page_size=50'
        )
        response = await make_get_request(url)
        body = await response.json()

        assert response.status == expected_answer['status']
        assert len(body) == expected_answer['length']