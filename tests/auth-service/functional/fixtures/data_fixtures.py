import json
import pytest
from typing import Any

from testdata.users import (
    superuser,
    weak_password_user,
    regular_users,
    disabled_user
)


@pytest.fixture
def superuser_data() -> dict[str, Any]:
    return superuser

@pytest.fixture
def weak_password_user_data() -> dict[str, Any]:
    return weak_password_user

@pytest.fixture
def regular_users_data() -> list[dict[str, Any]]:
    return regular_users

@pytest.fixture
def disabled_user_data() -> dict[str, Any]:
    return disabled_user