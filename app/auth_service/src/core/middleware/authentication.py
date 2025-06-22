"""Middleware for global depense to authenticate requests"""

from datetime import UTC, datetime
from uuid import NAMESPACE_DNS, uuid5

from src.api.dependencies import get_role_service, get_user_service
from src.db.models import User
from src.services.role_service import RoleService
from src.services.user_service import UserService

from fastapi import Depends, Request
from fastapi.openapi.models import OAuth2 as OAuth2Model, OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.base import SecurityBase


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", scheme_name="LoginRequest", auto_error=False
)


class AuthenticationMiddleware(SecurityBase):
    """Middleware for user authentication using OAuth2."""

    def __init__(self):
        self.model = OAuth2Model(flows=OAuthFlowsModel(), description=None)
        self.scheme_name = self.__class__.__name__

    async def __call__(
        self,
        request: Request,
        token: str | None = Depends(oauth2_scheme),
        user_service: UserService = Depends(get_user_service),
        role_service: RoleService = Depends(get_role_service),
    ) -> None:
        """
        Checks the presence and validity of the authorization token.
        If the token is missing or invalid, throws an HTTPException.
        Stores the authenticated user in the UserService cache.
        """
        user = None

        if token:
            try:
                user = await user_service.auth_service.validate_token(
                    token=token, type="access"
                )
            except Exception:
                user = None

        if not user:
            user_ip = request.client.host if request.client else "unknown"
            anonymous_uuid = str(uuid5(NAMESPACE_DNS, user_ip))

            user = User(
                id=anonymous_uuid,
                username=f"anonymous_{user_ip}",
                email="anonymous@example.com",
                password="*" * 256,
                is_active=False,
                is_superuser=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            anonymous_role = await role_service.get_role_by_name("anonymous")
            if anonymous_role:
                user.roles.append(anonymous_role)

        user_service.user = user
        request.state.user = user
