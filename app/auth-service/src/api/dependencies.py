"""API dependencies for dependency injection."""

from typing import Annotated

from jose import JWTError
from src.db.models.user import User
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.email_verification_service import EmailService

from fastapi import Depends, HTTPException, Request, status, Header
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_auth_service(request: Request) -> AuthService:
    """Get the authentication service from the container."""
    return request.app.container.auth_service()


def get_user_service(request: Request) -> UserService:
    """Get user service from the container."""
    return request.app.container.user_service()


def get_email_service(request: Request) -> EmailService:
    """Get email service from the container."""
    return request.app.container.email_service()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """
    Get the current authenticated user from the JWT token.


    Args:
        token: JWT token
        auth_service: Authentication service


    Returns:
        User: Current authenticated user


    Raises:
        HTTPException: If the token is invalid or the user is not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user = await auth_service.validate_token(token=token, type='access')
        if user is None:
            raise credentials_exception
        return user
    except JWTError as err:
        raise credentials_exception from err


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


async def get_private_user_service(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service)
):  
    user_service.user = await user_service.auth_service.validate_token(
        token=token, type='access')
    return user_service