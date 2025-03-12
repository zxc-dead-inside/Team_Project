"""API dependencies for dependency injection."""

from src.db.models.user import User
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.email_verification_service import EmailService

from fastapi import Depends, HTTPException, Request, status


def get_auth_service(request: Request) -> AuthService:
    """Get the authentication service from the container."""
    return request.app.container.auth_service()


def get_user_service(request: Request) -> UserService:
    """Get user service from the container."""
    return request.app.container.user_service()


def get_email_service(request: Request) -> EmailService:
    """Get email service from the container."""
    return request.app.container.email_service()


async def get_current_active_user(
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    Get the current active user.

    Args:
        user_service: Current user service

    Returns:
        User: Current active authenticated user

    Raises:
        HTTPException: If user is inactive
    """

    if not user_service.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user_service.user
