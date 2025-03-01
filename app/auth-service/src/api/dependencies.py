"""API dependencies for dependency injection."""

from typing import Annotated

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.user import User
from src.services.auth_service import AuthService
from src.services.email_verification import EmailVerifier
from src.services.redis_service import RedisService
from src.core.config import get_settings, Settings
from src.db.database import get_database, Database
from src.db.repositories.user_repository import UserRepository

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


async def get_user_repository(
    db: Database = Depends(get_database)
) -> UserRepository:
    """Dependency provider for UserRepository."""
    return UserRepository(db.session)


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


async def get_redis_service(
        settings: Settings = Depends(get_settings)
) -> RedisService:
    redis_service = RedisService(str(settings.redis_url))
    try:
        yield redis_service
    finally:
        await redis_service.close()


async def get_email_verifier(
        redis_service: RedisService = Depends(get_redis_service),
        settings: Settings = Depends(get_settings)
) -> EmailVerifier:
    return EmailVerifier(redis_service, settings)
