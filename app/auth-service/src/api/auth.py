import logging

from src.api.schemas.auth import (
    ForgotPasswordRequest, EmailConfirmation, ResetPasswordRequest, UserCreate
)
from src.services.auth_service import AuthService
from src.services.email_verification_service import EmailService
from src.services.redis_service import RedisService

from fastapi import APIRouter, Depends, HTTPException, Request, status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def get_auth_service(request: Request) -> AuthService:
    """Get auth service from the container."""
    return request.app.container.auth_service()


def get_email_service(request: Request) -> EmailService:
    """Get email service from the container."""
    return request.app.container.email_service()

def get_cache_service(request: Request) -> RedisService:
    """Get email service from the container."""
    return request.app.container.cache_service()


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


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service),
    cache_service: RedisService = Depends(get_cache_service)
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

    key = f"forgot_password:{request.email}"
    value = await cache_service.get(key)
    if value is None:
        current_requests = 0
    elif value.isdigit():
        current_requests = int(value)
    
    if current_requests >= 5:

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later."
        )
    await cache_service.set(key, current_requests, 30)
    

    user = await auth_service.user_repository.get_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    reset_token = email_service.create_confirmation_token(user.id, user.email)

    await email_service.send_reset_password_email(request.email, reset_token)

    current_requests += 1    
    return {
        "message": "We has sent an email to you. Check your mailbox please."
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
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

    success, message = await auth_service.reset_password(
        request.token, request.password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {"message": message}
