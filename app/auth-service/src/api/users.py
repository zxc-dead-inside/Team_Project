"""User profile and history endpoints."""

from datetime import datetime

from src.api.dependencies import get_current_active_user, get_user_service, require_permission
from src.api.schemas.user import (
    LoginHistoryItem,
    LoginHistoryResponse,
    PasswordUpdate,
    UsernameUpdate,
    UserProfile,
)
from src.db.models.user import User
from src.services.user_service import UserService

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/public")
async def get_profile(
        request: Request,
):
    current_user = request.state.user

    return {
        "user_id": str(current_user.id),
        "username": current_user.username,
    }


@router.get("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user profile.

    Returns:
        UserProfile: Current user profile
    """
    return current_user


@router.patch("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def update_username(
    username_update: UsernameUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update current user's username.

    Args:
        username_update: Username update data

    Returns:
        UserProfile: Updated user profile

    Raises:
        HTTPException: If username update fails
    """
    success, message, updated_user = await user_service.update_username(
        user_id=current_user.id,
        new_username=username_update.username,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return updated_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    password_update: PasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update current user's password.

    Args:
        password_update: Password update data

    Raises:
        HTTPException: If password update fails
    """
    success, message = await user_service.update_password(
        user_id=current_user.id,
        current_password=password_update.current_password,
        new_password=password_update.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    # No content response for successful password update
    return None


@router.get(
    "/me/history", response_model=LoginHistoryResponse, status_code=status.HTTP_200_OK
)
async def get_login_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    start_date: datetime | None = Query(
        None, description="Filter by start date (ISO format)"
    ),
    end_date: datetime | None = Query(
        None, description="Filter by end date (ISO format)"
    ),
    successful_only: bool | None = Query(
        None, description="Filter by successful logins"
    ),
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get current user's login history with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        size: Page size
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        successful_only: Optional filter for successful logins

    Returns:
        LoginHistoryResponse: Paginated login history
    """
    login_history, total = await user_service.get_login_history(
        user_id=current_user.id,
        page=page,
        size=size,
        start_date=start_date,
        end_date=end_date,
        successful_only=successful_only,
    )

    # Calculate total pages
    pages = (total + size - 1) // size if total > 0 else 1

    return LoginHistoryResponse(
        items=[LoginHistoryItem.model_validate(item) for item in login_history],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )
