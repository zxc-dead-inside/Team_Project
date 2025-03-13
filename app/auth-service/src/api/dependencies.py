"""API dependencies for dependency injection."""

from fastapi import Depends, HTTPException, Request, status

from src.db.models.user import User
from src.services.auth_service import AuthService
from src.services.email_verification_service import EmailService
from src.services.reset_password_service import ResetPasswordService
from src.services.user_service import UserService




def get_auth_service(request: Request) -> AuthService:
    """Get the authentication service from the container."""
    return request.app.container.auth_service()


def get_user_service(request: Request) -> UserService:
    """Get user service from the container."""
    return request.app.container.user_service()


def get_email_service(request: Request) -> EmailService:
    """Get email service from the container."""
    return request.app.container.email_service()

def get_reset_password_service(request: Request) -> ResetPasswordService:
    """Get reset password service from the container."""
    return request.app.container.reset_password_service()

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

    async def dependency(current_user: User = Depends(get_current_active_user)):
        if not await has_permission(current_user, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to perform this action. Missing permission: {permission_name}",
            )
        return current_user

    return dependency
