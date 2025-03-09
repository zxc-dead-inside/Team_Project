"""Authentication endpoints."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from http import HTTPStatus

from src.api.schemas.auth import EmailConfirmation, UserCreate
from src.api.dependencies import get_auth_service
from src.api.dependencies import get_email_service
from src.api.dependencies import get_current_active_user
from src.api.dependencies import get_user_service
from src.db.models.user import User
from src.models.login import LoginResponse
from src.services.auth_service import AuthService
from src.services.email_verification_service import EmailService
from src.services.user_service import UserService


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
# private_router = APIRouter(dependencies=[Depends(get_private_user_service)])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service),
):
    """Register a new user with email verification."""
    success, message, user = await auth_service.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    token = email_service.create_confirmation_token(user.id, user.email)

    await email_service.send_confirmation_email(user.email, token)

    return {
        "message": "User registered successfully. "
                   "Please confirm your email address.",
        "username": user.username,
        "email": user.email,
    }

@router.get("/confirm-email", status_code=status.HTTP_200_OK)
async def confirm_email_get(
    token: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Confirm user email via GET request (for email link)."""
    success, message = await auth_service.confirm_email(token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {"message": message}

@router.post("/confirm-email", status_code=status.HTTP_200_OK)
async def confirm_email_post(
    confirmation_data: EmailConfirmation,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Confirm user email via POST request (for API calls)."""
    success, message = await auth_service.confirm_email(confirmation_data.token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {"message": message}

@router.post("/token", response_model=dict, deprecated=True)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user and return access token.
    Args:
        form_data: OAuth2 form with username and password
    Returns:
        Dict with access token and token type
    Raises:
        HTTPException: If authentication fails
    """
    user = await auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        200: {'description': 'Login successful'},
        401: {'description': 'Invalid credentials'}
    }
)
async def login(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        user_service: UserService = Depends(get_user_service)
    ) -> LoginResponse:
    """
    Authenticate user and return access token.
    Args:
        form_data: OAuth2 form with username and password
    Returns:
        Dict with access token and token type
    Raises:
        HTTPException: If authentication fails
    """

    jwt_pair = await user_service.login_by_credentials(
        username=form_data.username, password=form_data.password,
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

@router.post(
    "/logout-other-devices",
    response_model=None,
    responses={
        200: {'description': 'You have successfully logged out'},
        401: {'description': 'You are not logged in'}
    }
)
async def logout_other_devices(
        current_user: User = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)

    ):
    """
    Logut user from other devices by changing token_version and return new jwt pair.
    """

    jwt_pair = await user_service.logout_from_all_device(current_user.id)
    return LoginResponse(
        access_token=jwt_pair.access_token,
        refresh_token=jwt_pair.refresh_token
    )

@router.post(
    "/refresh",
    response_model=None,
    responses={
        200: {'description': 'Tokens have been refreshed'},
        401: {'description': 'Invalid token'}
    }
)
async def refresh(
        Authorization: str = Header(),
        user_service: UserService = Depends(get_user_service)
    ):
    """
    Add received Refresh token to blacklist and retrun new JWT tokens pair.
    """
    refresh_token = Authorization.split(' ')[-1]
    jwt_pair = await user_service.refresh_token(refresh_token)
    return LoginResponse(
        access_token=jwt_pair.access_token,
        refresh_token=jwt_pair.refresh_token
    )
