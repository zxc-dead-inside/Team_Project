import uuid
from http import HTTPStatus
from typing import Any, Callable

import pytest
import pytest_asyncio
from settings import test_settings
from testdata.es_mapping import MOVIES_MAPPING


@pytest_asyncio.fixture
async def create_movie_index(create_index_factory: Callable):
    """Fixture to create movies index."""

    async def inner():
        await create_index_factory(
            test_settings.movie_index, MOVIES_MAPPING,recreate=True
        )
    return inner


@pytest.fixture
def movies_data() -> list[dict[str, Any]]:
    """Fixture providing test movie data with associated genres, directors, actors, and writers."""

    movie1_id = str(uuid.uuid4())
    movie2_id = str(uuid.uuid4())
    movie3_id = str(uuid.uuid4())

    fantastic = {"id": str(uuid.uuid4()), "name": "Фантастика"}
    drama = {"id": str(uuid.uuid4()), "name": "Драма"}
    adventure = {"id": str(uuid.uuid4()), "name": "Приключения"}
    crime = {"id": str(uuid.uuid4()), "name": "Криминал"}
    action = {"id": str(uuid.uuid4()), "name": "Боевик"}
    thriller = {"id": str(uuid.uuid4()), "name": "Триллер"}

    k_nolan = {"id": str(uuid.uuid4()), "name": "Кристофер Нолан"}
    m_mack = {"id": str(uuid.uuid4()), "name": "Мэттью МакКонахи"}
    e_hathaway = {"id": str(uuid.uuid4()), "name": "Энн Хэтэуэй"}
    j_chesteyn = {"id": str(uuid.uuid4()), "name": "Джессика Честейн"}
    d_nolan = {"id": str(uuid.uuid4()), "name": "Джонатан Нолан"}
    t_robbins = {"id": str(uuid.uuid4()), "name": "Тим Роббинс"}
    m_freeman = {"id": str(uuid.uuid4()), "name": "Морган Фриман"}
    f_darabont = {"id": str(uuid.uuid4()), "name": "Фрэнк Дарабонт"}
    s_king = {"id": str(uuid.uuid4()), "name": "Стивен Кинг"}
    k_bale = {"id": str(uuid.uuid4()), "name": "Кристиан Бэйл"}
    h_ledger = {"id": str(uuid.uuid4()), "name": "Хит Леджер"}
    a_ekhart = {"id": str(uuid.uuid4()), "name": "Аарон Экхарт"}

    return [
        {
            "_index": test_settings.movie_index,
            "_id": movie1_id,
            "_source": {
                "id": movie1_id,
                "imdb_rating": 8.6,
                "genres": [fantastic, drama, adventure],
                "title": "Интерстеллар",
                "description": "Фантастический фильм о путешествии сквозь червоточину в поисках нового дома для человечества.",
                "directors": [k_nolan],
                "actors": [m_mack, e_hathaway, j_chesteyn],
                "writers": [d_nolan],
                "actors_names": [
                    actor["name"] for actor in [m_mack, e_hathaway, j_chesteyn]
                ],
                "directors_names": [
                    director["name"] for director in [k_nolan]
                ],
                "writers_names": [
                    writer["name"] for writer in [d_nolan]
                ],
            },
        },
        {
            "_index": test_settings.movie_index,
            "_id": movie2_id,
            "_source": {
                "id": movie2_id,
                "imdb_rating": 9.3,
                "genres": [drama, crime],
                "title": "Побег из Шоушенка",
                "description": "История о надежде и силе духа, разворачивающаяся в тюрьме строгого режима.",
                "directors": [f_darabont],
                "actors": [t_robbins, m_freeman],
                "writers": [s_king],
                "actors_names": [actor["name"] for actor in [t_robbins, m_freeman]],
                "directors_names": [
                    director["name"] for director in [f_darabont]
                ],
                "writers_names": [
                    writer["name"] for writer in [s_king]
                ],
            },
        },
        {
            "_index": test_settings.movie_index,
            "_id": movie3_id,
            "_source": {
                "id": movie3_id,
                "imdb_rating": 9.0,
                "genres": [action, thriller, drama, adventure, fantastic],
                "title": "Тёмный рыцарь",
                "description": "Бэтмен должен остановить безумного преступника Джокера, который сеет хаос в Готэме.",
                "directors": [k_nolan],
                "actors": [k_bale, h_ledger, a_ekhart],
                "writers": [d_nolan],
                "actors_names": [
                    actor["name"] for actor in [k_bale, h_ledger, a_ekhart]
                ],
                "directors_names": [
                    director["name"] for director in [k_nolan]
                ],
                "writers_names": [
                    writer["name"] for writer in [d_nolan]
                ],
            },
        },
    ]

@pytest.mark.asyncio
class TestFilmAPI:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, es_write_data, create_movie_index, movies_data):
        """Setup test data"""

        await create_movie_index()
        await es_write_data(movies_data)

    async def test_films_popular_by_genre(self, make_get_request, movies_data):
        genre = movies_data[0]["_source"]["genres"][0]["id"]

        response = await make_get_request(
            f"{test_settings.movie_endpoint}/popular?genre={genre}&page_number=1&page_size=10"
        )
        data = await response.json()

        assert response.status == HTTPStatus.OK
        assert len(data) > 0
        assert "uuid" in data[0] and "title" in data[0]

    async def test_film_general(self, make_get_request):
        response = await make_get_request(
            f"{test_settings.movie_endpoint}/?page_number=1&page_size=10"
        )
        data = await response.json()

        assert response.status == HTTPStatus.OK
        assert len(data) > 0

    async def test_film_details(self, make_get_request, movies_data):
        film_id = movies_data[0]["_id"]

        response = await make_get_request(f"{test_settings.movie_endpoint}/{film_id}")
        data = await response.json()

        assert response.status == HTTPStatus.OK
        assert data["uuid"] == film_id

    async def test_film_details_not_found(self, make_get_request):
        response = await make_get_request(f"{test_settings.movie_endpoint}/non-existent-film-id")
        assert response.status == HTTPStatus.NOT_FOUND

    async def test_film_similar(self, make_get_request, movies_data):
        film_id = movies_data[0]["_id"]
        
        response = await make_get_request(f"{test_settings.movie_endpoint}/{film_id}/similar")
        data = await response.json()
        
        assert response.status == HTTPStatus.OK
        assert isinstance(data, list) and len(data) > 0

    async def test_film_sorting(self, make_get_request):
        response = await make_get_request(
            f"{test_settings.movie_endpoint}/?sort=-imdb_rating&page_number=1&page_size=10"
        )
        data = await response.json()        
        
        assert response.status == HTTPStatus.OK
        assert len(data) > 1
        assert all(data[i]["imdb_rating"] >= data[i + 1]["imdb_rating"] for i in range(len(data) - 1))

    async def test_film_search_query(self, make_get_request):
        response = await make_get_request(
            f"{test_settings.movie_endpoint}/search?query=Тёмный рыцарь&page_number=1&page_size=10"
        )
        data = await response.json()

        assert response.status == HTTPStatus.OK
        assert len(data) > 0
        assert any("Тёмный рыцарь" in film["title"] for film in data)
