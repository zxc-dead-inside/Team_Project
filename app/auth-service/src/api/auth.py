"""Authentication endpoints."""

import logging
from http import HTTPStatus

from fastapi import (
    APIRouter, Depends, HTTPException, Request, status, Header, Form
)
from fastapi.responses import RedirectResponse

from src.api.dependencies import (
    get_auth_service,
    get_email_service,
    get_user_service,
    get_reset_password_service,
    get_yandex_oauth_service,
)
from src.api.schemas.auth import (
    ForgotPasswordRequest, EmailConfirmation, ResetPasswordRequest, UserCreate,
    LoginRequest, LoginResponse
)
from src.core.logger import setup_logging
from src.services.auth_service import AuthService
from src.services.email_verification_service import EmailService
from src.services.user_service import UserService
from src.services.reset_password_service import ResetPasswordService
from src.services.yandex_oauth_service import YandexOAuthService

setup_logging()

public_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
private_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@public_router.post(
        "/register", status_code=status.HTTP_201_CREATED)
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

@public_router.get("/confirm-email", status_code=status.HTTP_200_OK)
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

@public_router.post("/confirm-email", status_code=status.HTTP_200_OK)
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

@public_router.post(
    "/login",
    responses={
        200: {'description': 'Login successful'},
        401: {'description': 'Invalid credentials'}
    }
)
async def login(
        request: Request,
        form_data: LoginRequest = Form(),
        user_service: UserService = Depends(get_user_service),
    ) -> LoginResponse:
    """
    Authenticate User with credentials and return jwt pair tokens.

    Args:
        Request: Raw request to get data for LoginHistory
        LoginRequest(username, password): Schema for User authentication with credentials
        UserService (Depends): User service for login by credentials

    Returns:
        Dict with access token and refresh token

    Raises:
        HTTPException: If authentication fails
    """

    jwt_pair: dict = await user_service.login_by_credentials(
        username=form_data.username, 
        password=form_data.password,
        request=request
    )

    if not jwt_pair:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Invalid credentials'
        )

    return LoginResponse(
        access_token=jwt_pair.get('access_token'),
        refresh_token=jwt_pair.get('refresh_token')
    )

@public_router.get("/auth/yandex")
async def yandex_auth_start(
    yandex_oauth_service: YandexOAuthService = Depends(get_yandex_oauth_service),
):
    try:
        state = yandex_oauth_service.generate_state()
        await yandex_oauth_service.save_state(f"oauth:yandex:{state}", 300)
        return RedirectResponse(
            url=yandex_oauth_service.get_auth_url(state),
            status_code=307  # Temporary Redirect
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@public_router.post("/login-via-yandex")
async def yandex_auth_start(
    request: Request,
    yandex_oauth_service: YandexOAuthService = Depends(get_yandex_oauth_service)
):
    # Генерируем и сохраняем state (например, в Redis)
    state = yandex_oauth_service.generate_state()
    await yandex_oauth_service.save_state(state)
    logging.info(f"YANDEX state: {state}")
    logging.info(yandex_oauth_service.get_auth_url(state))
    return {
        "auth_url": yandex_oauth_service.get_auth_url(state),
        "debug_message": "Use this URL in your browser for test purposes."
    }
    
    # return RedirectResponse(yandex_oauth_service.get_auth_url(state))

@public_router.get("/yandex/callback")
async def yandex_auth_callback(
    code: str,
    state: str,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    logging.info("YANDEX CALLBACK")
    try:
        tokens = await user_service.login_via_yandex(code, state, request)
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}
    
    if not tokens:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='...'
        )
    logging.info(f"tokens type: {type(tokens)}")
    logging.info(f"len tokens: {len(tokens)}")
    logging.info(f"tokens: {tokens}")
    return LoginResponse(
        access_token=tokens.get("access_token"),
        refresh_token=tokens.get("refresh_token"),
    )

@private_router.post(
    "/logout-other-devices",
    response_model=LoginResponse,
    responses={
        200: {'description': 'You have successfully logged out'},
        401: {'description': 'You are not logged in'}
    }
)
async def logout_other_devices(
        user_service: UserService = Depends(get_user_service)
    ):
    """
    Logut user from other devices by changing token_version and return new jwt pair.
    """

    jwt_pair: dict = await user_service.logout_from_all_device()

    return LoginResponse(
        access_token=jwt_pair.get('access_token'),
        refresh_token=jwt_pair.get('refresh_token')
    )

@public_router.post(
    "/refresh",
    response_model=LoginResponse,
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
    jwt_pair: dict = await user_service.refresh_token(refresh_token)
    return LoginResponse(
        access_token=jwt_pair.get('access_token'),
        refresh_token=jwt_pair.get('refresh_token')
    )

@public_router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    reset_password_service: ResetPasswordService = Depends(
        get_reset_password_service)
):
    """
    Checks if an email is registered and sends an email with reset token.

    Args: 
        request: Dict with an email
    
    Reterns:
        Dict with information message

    Raises:
        HTTPException: If an email is not registered
    """

    state, result = await reset_password_service.check_requests(request.email)
    if not state and result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reset password service unavalable. Please try again later."
        )
    
    if result and not state:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result
        )

    user = await auth_service.user_repository.get_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    reset_token = reset_password_service.create_reset_token(
        user.id, user.email
    )
    await reset_password_service.send_reset_password_email(
        request.email, reset_token
    )
    await reset_password_service.increase_requests(request.email)

    return {
        "message": "We have sent an email to you. Check your mailbox please."
    }


@private_router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    reset_password_service: ResetPasswordService = Depends(
        get_reset_password_service)
):
    """
    Change password for user if token is valid.

    Args:
        request: Dict with token and new password
    
    Reterns:
        Dict with information message

    Raises:
        HTTPException: if token is invalid or password is simple
    
    """

    success, message = await reset_password_service.reset_password(
        request.token, request.password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {"message": message}
