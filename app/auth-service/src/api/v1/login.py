from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from http import HTTPStatus

from src.core.decorators.public_pass import public_endpoint
from src.models.login import LoginRequest, LoginResponse
from src.services.di import get_login_service
from src.services.login import LoginService


router = APIRouter()

@public_endpoint
@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        200: {'description': 'Login successful'},
        401: {'description': 'Invalid credentials'}
    }
)
@inject
async def login(
        login_request: LoginRequest,
        login_service: LoginService = Depends(get_login_service)
    ) -> LoginResponse:
    """
    Login endpoint for user authorization.

    Returns:
        LoginResponse: User`s Access and Refresh tokens.
    """

    jwt_pair = await login_service.login_by_credentials_and_return_jwt_pair(
        username=login_request.username, password=login_request.password
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
