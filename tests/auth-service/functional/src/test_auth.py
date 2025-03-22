from aiohttp import ClientResponse
from http import HTTPStatus
import pytest


@pytest.mark.asyncio
class TestAuth:
    async def test_healtcheck(self, make_get_request):
        response: ClientResponse = await make_get_request(url='/api/health')
        data: dict = await response.json()

        assert response.status == HTTPStatus.OK
        assert data.get('status') == 'healthy'
        for component in data.get('components').values():
            assert component == 'healthy'
    
    async def test_register_superuser(self, make_post_request, superuser_data):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/register',
            json=superuser_data
        )
        assert response.status == HTTPStatus.CREATED

    async def test_register_already_registered_user(
            self, make_post_request, superuser_data: dict):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/register',
            json=superuser_data
        )
        data: dict = await response.json()

        assert response.status == HTTPStatus.BAD_REQUEST
        assert data.get('detail') == 'Username already exists'

    async def test_register_weak_password_user(
            self, make_post_request, weak_password_user_data: dict):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/register',
            json=weak_password_user_data
        )
        data: dict = await response.json()

        assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY
        assert data.get('detail')[-1].get('type') == 'string_too_short'
    
    async def test_register_disabled_user(
            self, make_post_request, disabled_user_data: dict):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/register',
            json=disabled_user_data
        )

        assert response.status == HTTPStatus.CREATED
    
    async def test_register_regular_users(
            self, make_post_request, regular_users_data: list[dict]):
        responses: list[ClientResponse] = [
            await make_post_request(
                url='/api/v1/auth/register',
                json=user
            ) for user in regular_users_data
        ]
        for response in responses:
            assert response.status == HTTPStatus.CREATED
    
    async def test_login_user(
            self, make_post_request, admin_data: dict):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/login',
            data = {
                'username': admin_data.get('username'),
                'password': admin_data.get('password')
            }
        )
        data: dict = await response.json()
        
        assert response.status == HTTPStatus.OK
        assert data.get('access_token')
        assert data.get('refresh_token')
        assert data.get('token_type')
    
    async def test_login_user_wrong_creds(
            self, make_post_request, superuser_data: dict):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/login',
            data = {
                'username': superuser_data.get('username'),
                'password': 'password'
            }
        )
        data: dict = await response.json()
        
        assert response.status == HTTPStatus.UNAUTHORIZED
        assert data.get('detail') == 'Invalid credentials'
    
    async def test_login_disabled_user(
            self, make_post_request, disabled_user_data: dict):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/login',
            data = {
                'username': disabled_user_data.get('username'),
                'password': disabled_user_data.get('password')
            }
        )
        data: dict = await response.json()
        
        assert response.status == HTTPStatus.UNAUTHORIZED
        assert data.get('detail') == 'Invalid credentials'

    async def test_forgot_password(
            self, make_post_request, superuser_data: dict):
        response: ClientResponse = await make_post_request(
            url='/api/v1/auth/forgot-password',
            json = {'email': superuser_data.get('email')}
        )
        data: dict = await response.json()
        
        assert response.status == HTTPStatus.OK
        assert data.get('message') == 'We have sent an email to you. Check your mailbox please.'

    async def test_logout_other_devices(
        self, make_post_request, make_get_request, admin_data: dict):
        responses = [
            await make_post_request(
                url='/api/v1/auth/login',
                data = {
                    'username': admin_data.get('username'),
                    'password': admin_data.get('password')
                }
            ) for _ in range(3)
        ]

        tokens = [await response.json() for response in responses]

        for token in tokens:
            response: ClientResponse = await make_get_request(
                url='/api/v1/users/me',
                headers={
                    'Authorization': f'Bearer {token.get("access_token")}'
                }
            )
            data: dict = await response.json()

            assert response.status == HTTPStatus.OK
            assert data.get('username') == admin_data.get('username')
        
        response = await make_post_request(
            url='/api/v1/auth/logout-other-devices',
            headers={
                'Authorization': f'Bearer {tokens[-1].get("access_token")}'
            }
        )
        data: dict = await response.json()

        response: ClientResponse = await make_get_request(
            url='/api/v1/users/me',
            headers={'Authorization': f'Bearer {data.get("access_token")}'}
        )
        data: dict = await response.json()

        assert response.status == HTTPStatus.OK
        assert data.get('username') == admin_data.get('username')

        for token in tokens:
            response: ClientResponse = await make_get_request(
                url='/api/v1/users/me',
                headers={
                    'Authorization': f'Bearer {token.get("access_token")}'
                }
            )
            data: dict = await response.json()

            assert response.status == HTTPStatus.UNAUTHORIZED
            assert data.get('detail') == 'Invalid token'
