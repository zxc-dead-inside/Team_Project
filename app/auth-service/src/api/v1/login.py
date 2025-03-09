from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from http import HTTPStatus

from src.models.login import LoginRequest, LoginResponse
from src.services.di import get_user_service
from src.services.di import get_private_user_service
from src.services.di import oauth2_scheme
from src.services.user_service import UserService


public_router = APIRouter()
private_router = APIRouter(dependencies=[Depends(get_private_user_service)])

@inject
@public_router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        200: {'description': 'Login successful'},
        401: {'description': 'Invalid credentials'}
    }
)
async def login(
        login_request: LoginRequest,
        request: Request,
        user_service: UserService = Depends(get_user_service)
    ) -> LoginResponse:
    """
    Login endpoint for user authorization.

    Returns:
        LoginResponse: User`s Access and Refresh tokens.
    """

    jwt_pair = await user_service.login_by_credentials(
        username=login_request.username, password=login_request.password,
        request=request
    )

    if not jwt_pair:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Invalid credentials'
        )

    return LoginResponse(
        access_token=jwt_pair.access_token,
        refresh_token=jwt_pair.refresh_token
    )

@private_router.post(
    "/logout",
    response_model=None,
    responses={
        200: {'description': 'You have successfully logged out'},
        401: {'description': 'You are not logged in'}
    }
)
@inject
async def logout(
        user_service: UserService = Depends(get_user_service)
    ):
    jwt_pair = await user_service.logout_from_all_device()
    return LoginResponse(
        access_token=jwt_pair.access_token,
        refresh_token=jwt_pair.refresh_token
    )

@public_router.post(
    "/refresh",
    response_model=None,
    responses={
        200: {'description': 'You have successfully logged out'},
        401: {'description': 'You are not logged in'}
    }
)
@inject
async def refresh(
        refresh_token: OAuth2PasswordBearer = Depends(oauth2_scheme),
        user_service: UserService = Depends(get_user_service)
    ):
    jwt_pair = await user_service.refresh_token(refresh_token)
    return LoginResponse(
        access_token=jwt_pair.access_token,
        refresh_token=jwt_pair.refresh_token
    )
