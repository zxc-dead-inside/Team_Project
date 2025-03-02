from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from functools import lru_cache

from src.core.container import Container
from src.services.login import LoginService
from src.services.auth_service import AuthService


@lru_cache()
@inject
def get_login_service(
        auth_service: AuthService = Depends(Provide[Container.auth_service])
) -> LoginService:
    return LoginService(auth_service=auth_service)
