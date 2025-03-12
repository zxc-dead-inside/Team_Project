"""Middleware for global depense to authenticate requests"""

from fastapi import Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer

from src.api.dependencies import get_user_service
from src.services.user_service import UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def AuthenticationMiddlewareService(
        request: Request,
        user_service: UserService = Depends(get_user_service)
    ) -> None:
    """
    Dependensy for authenticate every request if requested path is not 
    in public paths or requested path starts with private path prefixes 

    Args:
        token: JWT token

    Returns: None

    Raises:
        HTTPException: If the token is missing
    """

    public_paths = request.app.container.config().get('public_paths', None)
    private_path_prefixes = request.app.container.config().get(
        'private_path_prefixes', None)

    # Pass authentication if url.path is included in public paths config
    if request.url.path in public_paths:
        return None
    else:
        # Authentication if url.path is included in private path prefixes config
        if private_path_prefixes:
            for prefix in private_path_prefixes:
                if request.url.path.startswith(prefix):
                    token: str = await oauth2_scheme(request)
                    if not token:
                        raise HTTPException(
                            status_code=401,
                            detail="Authorization token missing"
                        )
                    
                    # Save authenticated User to cashed UserService
                    user_service.user = await user_service.auth_service.validate_token(
                        token=token, type='access')
                    return None
        else:
            raise HTTPException(
                status_code=500, detail="Something went wrong...")
