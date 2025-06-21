"""API endpoints for role management."""

from uuid import UUID

from src.api.dependencies import get_current_active_user
from src.api.schemas.roles import RoleCreate, RoleListResponse, RoleResponse, RoleUpdate
from src.db.models.user import User
from src.services.auth_service import AuthService
from src.services.role_service import RoleService

from fastapi import APIRouter, Depends, HTTPException, Request, status


router = APIRouter(prefix="/api/v1/roles", tags=["Roles"])


def get_role_service(request: Request) -> RoleService:
    """Get role service from the container."""
    return request.app.container.role_service()


def get_auth_service(request: Request) -> AuthService:
    """Get auth service from the container."""
    return request.app.container.auth_service()


async def has_permission(user: User, permission_name: str) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: User object
        permission_name: Permission name to check

    Returns:
        bool: True if user has permission, False otherwise
    """
    # If the user is an admin, they have all permissions
    if hasattr(user, "roles") and user.roles:
        if any(role.name == "admin" for role in user.roles):
            return True

        # Check if the user has the specific permission through any of their roles
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


@router.get(
    "",
    response_model=RoleListResponse,
    summary="List all roles",
)
async def list_roles(
    role_service: RoleService = Depends(get_role_service),
    _: User = Depends(require_permission("role_read")),
):
    """
    Get a list of all roles.

    Requires role_read permission.
    """
    roles = await role_service.get_all_roles()
    return RoleListResponse(roles=roles, total=len(roles))


@router.get("/{role_id}", response_model=RoleResponse, summary="Get role by ID")
async def get_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    _: User = Depends(require_permission("role_read")),
):
    """
    Get a specific role by ID.

    Requires role_read permission.
    """
    role = await role_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found",
        )
    return role


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
)
async def create_role(
    role_data: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
    _: User = Depends(require_permission("role_create")),
):
    """
    Create a new role.

    Requires role_create permission.
    """
    success, message, role = await role_service.create_role(role_data)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return role


@router.put("/{role_id}", response_model=RoleResponse, summary="Update a role")
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    role_service: RoleService = Depends(get_role_service),
    _: User = Depends(require_permission("role_update")),
):
    """
    Update an existing role.

    Requires role_update permission.
    """
    success, message, role = await role_service.update_role(role_id, role_data)

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

    return role


@router.delete(
    "/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a role"
)
async def delete_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    _: User = Depends(require_permission("role_delete")),
):
    """
    Delete a role.

    Requires role_delete permission.
    System roles (admin, user) cannot be deleted.
    """
    success, message = await role_service.delete_role(role_id)

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

    return None
