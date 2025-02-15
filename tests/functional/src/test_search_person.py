import uuid
from http import HTTPStatus
from typing import Any

import pytest
import pytest_asyncio
from testdata.es_mapping import es_indices_settings
from settings import test_settings

def person_data() -> list[dict[str, Any]]:
    """Fixture providing test movie data for searching purpose."""

    film_id = str(uuid.uuid4())
    person_id = str(uuid.uuid4())

    return {
        "id": person_id,
        "full_name": "Anne Hathaway",
        "films": [{"id": film_id, "roles": ["actor"]}],
    }

class TestPersonSearchAPI:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, es_create_index, es_write_data):
        """Setup test data."""

        await es_create_index(
            test_settings.person_index,
            es_indices_settings.persons_settings,
            es_indices_settings.persons_mapping
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
        url = test_settings.person_search_endpoint.substitute(
            search=query_data['search'])
        response = await make_get_request(url)
        body = await response.json()

        assert response.status == expected_answer['status']
        assert len(body) == expected_answer['length']