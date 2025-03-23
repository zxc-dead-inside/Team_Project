import pytest
from utils.helpers import setup_logger

logger = setup_logger("postgres_fixtures")


class TestAuthRegister:
    valid_user_data = {
        "username": "string",
        "email": "user@example.com",
        "is_active": True,
        "is_superuser": False,
        "password": "P@ssw0rd",
        "role_ids": []
    }

    @pytest.mark.asyncio
    async def test_successful_registration(self, make_post_request):
        response = await make_post_request(
            url="/api/v1/auth/register",
            data=self.valid_user_data,
        )
        logger.info(f"RESPONSE: {response}")
        assert response.status == 201
