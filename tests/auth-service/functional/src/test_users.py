from aiohttp import ClientResponse
from http import HTTPStatus
import pytest


@pytest.mark.asyncio
class TestUsers:
    async def test_me(
            self, make_post_request, make_get_request, superuser_data):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/login',
            data = {
                'username': superuser_data.get('username'),
                'password': superuser_data.get('password')
            }
        )
        data: dict = await response.json()

        response: ClientResponse = await make_get_request(
            url='/api/v1/users/me',
            headers={'Authorization': f'Bearer {data.get("access_token")}'}
        )
        data: dict = await response.json()

        assert response.status == HTTPStatus.OK
        assert data.get('email') == superuser_data.get('email')

    async def test_history(
            self, make_post_request, make_get_request, superuser_data):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/login',
            data = {
                'username': superuser_data.get('username'),
                'password': superuser_data.get('password')
            }
        )
        data: dict = await response.json()

        response: ClientResponse = await make_get_request(
            url='/api/v1/users/me/history?page=1&size=10',
            headers={'Authorization': f'Bearer {data.get("access_token")}'}
        )
        data: dict = await response.json()

        assert response.status == HTTPStatus.OK
        assert len(data.get('items')) > 1
        assert data.get('items')[0].get('successful') == 'Y'
