"""Middleware for global depense to authenticate requests"""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.base import SecurityBase
from fastapi.openapi.models import OAuth2 as OAuth2Model
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from src.api.dependencies import get_user_service
from src.services.user_service import UserService


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="LoginRequest"
)


class AuthenticationMiddleware(SecurityBase):
    """Middleware for user authentication using OAuth2."""
    def __init__(self):
        self.model = OAuth2Model(
            flows=OAuthFlowsModel(), description=None
        )
        self.scheme_name = self.__class__.__name__
    async def __call__(
            self,
            token: str = Depends(oauth2_scheme),
            user_service: UserService = Depends(get_user_service)
    ) -> None:
        """
        Checks the presence and validity of the authorization token.
        If the token is missing or invalid, throws an HTTPException.
        Stores the authenticated user in the UserService cache.
        """
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Authorization token missing"
            )

        # Saving authenticated User to cashed UserService
        user_service.user = await user_service.auth_service.validate_token(
            token=token, type='access')
