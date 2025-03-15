"""Authentication endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from src.api.schemas.auth import (
    ForgotPasswordRequest, EmailConfirmation, ResetPasswordRequest, UserCreate
)
from src.api.dependencies import get_current_user, has_permission, oauth2_scheme
from src.api.decorators import requires_permissions
from src.db.models.user import User
from src.core.logger import setup_logging
from src.services.auth_service import AuthService
from src.services.email_verification_service import EmailService
from src.services.reset_password_service import ResetPasswordService
from src.services.user_service import UserService


from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials

setup_logging()


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def get_auth_service(request: Request) -> AuthService:
    """Get auth service from the container."""
    return request.app.container.auth_service()


def get_email_service(request: Request) -> EmailService:
    """Get email service from the container."""
    return request.app.container.email_service()

def get_reset_password_service(request: Request) -> ResetPasswordService:
    """Get reset password service from the container."""
    return request.app.container.reset_password_service()

def get_user_service(request: Request) -> UserService:
    """Get user service from the container."""
    return request.app.container.user_service()


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


@router.post("/token", response_model=dict)
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

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    reset_password_service: ResetPasswordService = Depends(get_reset_password_service)
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


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    reset_password_service: ResetPasswordService = Depends(get_reset_password_service)
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


@router.get(
    "/check-permission",
    summary="Check if user has a specific permission",
    response_model=dict[str, bool],
)
async def check_permission_endpoint(
    permission_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, bool]:
    """
    Checks if a user has permission.
    Authentication is needed.

    Args:
        Permistion name, current user

    Reterns:
        True if a user has permission.
    
    Raises:
        HTTPException: Unauthorized
    """
    
    permission = await has_permission(current_user, permission_name)
    return {"has_permission": permission}

@router.get("/check-permission")
async def check_permission(
    permission_name: str,
    request: Request,
#    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Checks if a user has permission.
    Authentication is needed.

    Args:
        Permission name, request

    Reterns:
        Dict[str, bool]: True if a user has permission.
    
    Raises:
        HTTPException: Unauthorized
    """

    logging.info("Checking permisson")

    # if not credentials:
    #     raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    # logging.info(f"credentials: {credentials}")
    
    token = request.headers.get("Authorization", "").split("Bearer ")[-1]
    # if len(token) == 0:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Unauthorized"
    #     )
    logging.info(f"token: {token}")
    
    payload = await auth_service.return_payload_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
   
    user_id = UUID(payload.get("sub"))
    success, msg, permissions = await user_service.get_user_permissions(user_id)

    if not success:
        raise HTTPException(status_code=404, detail=msg)

    return {"has_permission": permission_name in permissions}
