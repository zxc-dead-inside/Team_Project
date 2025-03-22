from aiohttp import ClientResponse
from http import HTTPStatus
import pytest


@pytest.mark.asyncio
class TestSuperUsers:
    async def test_superusers(
            self,
            make_post_request,
            make_get_request,
            admin_data
    ):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/login',
            data = {
                'username': admin_data.get('username'),
                'password': admin_data.get('password')
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
