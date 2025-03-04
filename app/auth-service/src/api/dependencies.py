"""API dependencies for dependency injection."""

from typing import Annotated

from jose import JWTError
from src.models.user import User
from src.services.auth_service import AuthService

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_auth_service() -> AuthService:
    """
    Get the authentication service from the container.

    Returns:
        AuthService: Authentication service
    """
    from src.main import app

    return app.container.auth_service()


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
        user = await auth_service.validate_token(token)
        if user is None:
            raise credentials_exception
        return user
    except JWTError as err:
        raise credentials_exception from err
