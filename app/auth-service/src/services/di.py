from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from functools import lru_cache

from fastapi.security import OAuth2PasswordBearer

from src.core.container import Container
from src.services.auth_service import AuthService
from src.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@lru_cache()
@inject
def get_public_user_service(
        auth_service: AuthService = Depends(Provide[Container.auth_service])
) -> UserService:
    return UserService(auth_service=auth_service)

@lru_cache()
@inject
def get_user_service(
        auth_service: AuthService = Depends(Provide[Container.auth_service])
) -> UserService:
    return UserService(auth_service=auth_service)

async def get_protected_user_service(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service)
):  
    user_service.user = await user_service.auth_service.validate_token(
        token=token, type='access')

    return user_service