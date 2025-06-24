from uuid import UUID

from src.api.dependencies import get_auth_service, get_user_service, require_permission
from src.api.schemas.user_roles import (
    BulkRoleAssignment,
    RoleAssignment,
    UserRoleResponse,
)
from src.db.models.user import User
from src.services.auth_service import AuthService
from src.services.user_service import UserService

from fastapi import APIRouter, Depends, HTTPException, status


router = APIRouter(prefix="/api/v1/users", tags=["User Roles"])


@router.get(
    "/{user_id}/roles",
    response_model=UserRoleResponse,
    summary="Get user roles",
)
async def get_user_roles(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    _: User = Depends(require_permission("user_read")),
):
    """
    Get all roles assigned to a user.

    Requires user_read permission.
    """
    success, message, response = await user_service.get_user_roles(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )

    return response


@router.post(
    "/{user_id}/roles",
    response_model=UserRoleResponse,
    summary="Assign a role to a user",
)
async def assign_role(
    user_id: UUID,
    role_data: RoleAssignment,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_permission("user_update")),
):
    """
    Assign a role to a user.

    Requires user_update permission.
    """
    success, message, user = await user_service.assign_role_to_user(
        user_id, role_data.role_id
    )

    if not success:
        if "not found" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            )

    success, _, response = await user_service.get_user_roles(user_id)

    if user_id == current_user.id:
        tokens = await auth_service.refresh_tokens_for_user(user)
        # Add tokens to the response
        response_dict = response.model_dump()
        response_dict.update({"tokens": tokens})
        return response_dict

    return response


@router.post(
    "/{user_id}/roles/bulk",
    response_model=UserRoleResponse,
    summary="Assign multiple roles to a user",
)
async def bulk_assign_roles(
    user_id: UUID,
    role_data: BulkRoleAssignment,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_permission("user_update")),
):
    """
    Assign multiple roles to a user.

    Requires user_update permission.
    """
    success, message, user = await user_service.bulk_assign_roles(
        user_id, role_data.role_ids
    )

    if not success:
        if "not found" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            )

    success, _, response = await user_service.get_user_roles(user_id)

    if user_id == current_user.id:
        tokens = await auth_service.refresh_tokens_for_user(user)
        response_dict = response.model_dump()
        response_dict.update({"tokens": tokens})
        return response_dict

    return response


@router.delete(
    "/{user_id}/roles/{role_id}",
    response_model=UserRoleResponse,
    summary="Remove a role from a user",
)
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_permission("user_update")),
):
    """
    Remove a role from a user.

    Requires user_update permission.
    """
    success, message, user = await user_service.remove_role_from_user(user_id, role_id)

    if not success:
        if "not found" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            )

    success, _, response = await user_service.get_user_roles(user_id)

    if user_id == current_user.id:
        tokens = await auth_service.refresh_tokens_for_user(user)
        # Add tokens to the response
        response_dict = response.model_dump()
        response_dict.update({"tokens": tokens})
        return response_dict

    return response
