"""API dependencies for dependency injection."""

from typing import Annotated

from jose import JWTError
from src.db.models.user import User
from src.services.auth_service import AuthService
from src.services.user_service import UserService

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_auth_service(request: Request) -> AuthService:
    """Get the authentication service from the container."""
    return request.app.container.auth_service()


def get_user_service(request: Request) -> UserService:
    """Get user service from the container."""
    return request.app.container.user_service()


async def get_current_user(request: Request) -> User:
    """
    Получает текущего пользователя из middleware.
    """
    return request.state.user



async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return current_user


async def has_permission(user: User, permission_name: str) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: User object
        permission_name: Permission name to check

    Returns:
        bool: True if user has permission, False otherwise
    """

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
