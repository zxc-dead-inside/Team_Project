"""API endpoints for superuser management."""

from typing import Annotated
from uuid import UUID

from src.api.dependencies import (
    get_superuser_service,
    require_superuser,
)
from src.api.schemas.superuser import (
    AuditLogResponse,
    SuperuserListResponse,
    SuperuserResponse,
)
from src.db.models.user import User
from src.services.superuser_service import SuperuserService

from fastapi import APIRouter, Depends, HTTPException, Request, status


router = APIRouter(prefix="/superusers", tags=["Super Users"])


@router.get(
    "/",
    response_model=SuperuserListResponse,
    summary="List all superusers",
)
async def list_superusers(
    superuser_service: Annotated[SuperuserService, Depends(get_superuser_service)],
    _: Annotated[User, Depends(require_superuser)],
):
    """
    List all superusers in the system.

    Only accessible to superusers.
    """
    superusers = await superuser_service.list_superusers()

    return {
        "superusers": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": [role.name for role in user.roles] if user.roles else [],
            }
            for user in superusers
        ],
        "total": len(superusers),
    }


@router.post(
    "/grant/{user_id}",
    response_model=SuperuserResponse,
    summary="Grant superuser privileges",
)
async def grant_superuser(
    user_id: UUID,
    request: Request,
    superuser_service: Annotated[SuperuserService, Depends(get_superuser_service)],
    current_user: Annotated[User, Depends(require_superuser)],
):
    """
    Grant superuser privileges to a user.

    Only accessible to superusers.
    """
    client_host = request.client.host if request.client else None

    success, message, _ = await superuser_service.grant_superuser(
        user_id=user_id,
        granted_by=current_user.id,
        ip_address=client_host,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {"message": message}


@router.post(
    "/revoke/{user_id}",
    response_model=SuperuserResponse,
    summary="Revoke superuser privileges",
)
async def revoke_superuser(
    user_id: UUID,
    request: Request,
    superuser_service: Annotated[SuperuserService, Depends(get_superuser_service)],
    current_user: Annotated[User, Depends(require_superuser)],
):
    """
    Revoke superuser privileges from a user.

    Only accessible to superusers.
    """
    # Prevent revoking own superuser privileges
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own superuser privileges",
        )

    client_host = request.client.host if request.client else None

    success, message, _ = await superuser_service.revoke_superuser(
        user_id=user_id,
        revoked_by=current_user.id,
        ip_address=client_host,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {"message": message}


@router.get(
    "/audit-log",
    response_model=AuditLogResponse,
    summary="Get superuser audit log",
)
async def get_audit_log(
    superuser_service: Annotated[SuperuserService, Depends(get_superuser_service)],
    _: Annotated[User, Depends(require_superuser)],
    page: int = 1,
    size: int = 20,
):
    """
    Get audit log entries for superuser actions.

    Only accessible to superusers.
    """
    logs, total = await superuser_service.get_superuser_audit_log(
        page=page,
        size=size,
    )

    return {
        "logs": logs,
        "total": total,
        "page": page,
        "size": size,
    }
