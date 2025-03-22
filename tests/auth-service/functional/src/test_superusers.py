from aiohttp import ClientResponse
from http import HTTPStatus
import pytest


@pytest.mark.asyncio
class TestSuperUsers:
    async def test_superusers(
            self,
            make_post_request,
            make_get_request,
            superuser_data,
            disabled_user_data
    ):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/login',
            data = {
                'username': superuser_data.get('username'),
                'password': superuser_data.get('password')
            }
        )
        data: dict = await response.json()

        response: ClientResponse = await make_get_request(
            url='/superusers/',
            headers={'Authorization': f'Bearer {data.get("access_token")}'}
        )
        data: dict = await response.json()

        assert response.status == HTTPStatus.OK
        assert len(data.get('superusers')) >= 1

        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/login',
            data = {
                'username': disabled_user_data.get('username'),
                'password': disabled_user_data.get('password')
            }
        )
        data: dict = await response.json()

        response: ClientResponse = await make_get_request(
            url='/superusers/',
            headers={'Authorization': f'Bearer {data.get("access_token")}'}
        )
        data: dict = await response.json()

        assert response.status == HTTPStatus.FORBIDDEN
        assert data.get('detail') == 'Inactive user'
