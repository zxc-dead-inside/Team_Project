"""API dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from src.db.models.user import User
from src.services.auth_service import AuthService
from src.services.email_verification_service import EmailService
from src.services.reset_password_service import ResetPasswordService
from src.services.superuser_service import SuperuserService
from src.services.user_service import UserService
from src.services.role_service import RoleService
from src.services.yandex_oauth_service import YandexOAuthService


def get_auth_service(request: Request) -> AuthService:
    """Get the authentication service from the container."""
    return request.app.container.auth_service()


def get_user_service(request: Request) -> UserService:
    """Get user service from the container."""
    return request.app.container.user_service()


def get_role_service(request: Request) -> RoleService:
    """Get role service from the container."""
    return request.app.container.role_service()


def get_email_service(request: Request) -> EmailService:
    """Get email service from the container."""
    return request.app.container.email_service()


def get_superuser_service(request: Request) -> SuperuserService:
    """Get superuser service from the container."""
    return request.app.container.superuser_service()


def get_reset_password_service(request: Request) -> ResetPasswordService:
    """Get reset password service from the container."""
    return request.app.container.reset_password_service()


def get_yandex_oauth_service(request: Request) -> YandexOAuthService:
    """Get Yandex OAuth service from the container."""
    return request.app.container.yandex_oauth_service()


async def get_current_user(request: Request) -> User:
    """
    Получает текущего пользователя из middleware.
    """
    return request.state.user


async def get_current_active_user(
    user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.

    Args:
        user: Current user

    Returns:
        User: Current active authenticated user or anonymus

    Raises:
        HTTPException: If user is inactive
    """

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def has_permission(user: User, permission_name: str) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: User object
        permission_name: Permission name to check

    Returns:
        bool: True if user has permission, False otherwise
    """

    if user.is_superuser:
        return True

    if hasattr(user, "roles") and user.roles:
        if any(role.name == "admin" for role in user.roles):
            return True

        for role in user.roles:
            if hasattr(role, "permissions") and role.permissions:
                for permission in role.permissions:
                    if permission.name == permission_name:
                        return True

    return False


def require_permission(permission_name: str):
    """Dependency factory for permission-based access control."""

    async def dependency(current_user: User = Depends(get_current_user)):
        if not await has_permission(current_user, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to perform this action. Missing permission: {permission_name}",
            )
        return current_user

    return dependency


def require_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Dependency to ensure user is a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires superuser privileges",
        )
    return current_user
