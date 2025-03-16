from fastapi import (
    APIRouter,
    Request,
    status
)
from src.api.decorators.permissions_checker import required


router = APIRouter(prefix='/demo', tags=['Demonstration'])


@router.get(
    '/whoami', status_code=status.HTTP_200_OK
)
async def whoami(request: Request):
    user = getattr(request.state, "user", None)

    if user: return user
    else: return 'You are not identified user.'

@router.get(
    '/role_admin', status_code=status.HTTP_200_OK
)
@required(roles=['admin'])
async def role_admin(request: Request):
    user = getattr(request.state, "user", None)

    if user: return request.state.user
    else: return 'You are not identified user.'

@router.get(
    '/role_moderator', status_code=status.HTTP_200_OK
)
@required(roles=['moderator'])
async def role_moderator(request: Request):
    user = getattr(request.state, "user", None)

    if user: return request.state.user
    else: return 'You are not identified user.'

@router.get(
    '/role_admin_or_moderator', status_code=status.HTTP_200_OK
)
@required(roles=['admin', 'moderator'])
async def role_admin_or_moderator(request: Request):
    user = getattr(request.state, "user", None)

    if user: return request.state.user
    else: return 'You are not identified user.'

@router.get(
    '/permissions_content_all', status_code=status.HTTP_200_OK
)
@required(permissions=['content_all'])
async def permissions_user_create(request: Request):
    user = getattr(request.state, "user", None)

    if user: return request.state.user
    else: return 'You are not identified user.'

@router.get(
    '/permissions_content_all', status_code=status.HTTP_200_OK
)
@required(permissions=['content_all'])
async def permissions_user_create(request: Request):
    user = getattr(request.state, "user", None)

    if user: return request.state.user
    else: return 'You are not identified user.'

@router.get(
    '/anonym-allowed', status_code=status.HTTP_200_OK
)
@required(roles=['moderator'], anonymous_allowed=True)
async def permissions_user_create(request: Request):
    user = getattr(request.state, "user", None)

    if user: return request.state.user
    else: return 'You are not identified user.'
