from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field


class RoleAssignment(BaseModel):
    """Schema for role assignment to a user."""
    role_id: UUID


class BulkRoleAssignment(BaseModel):
    """Schema for bulk role assignment to a user."""
    role_ids: Annotated[list[UUID], Field(..., min_items=1)]


class UserRoleResponse(BaseModel):
    """Response schema for user-role assignments."""
    user_id: UUID
    role_ids: list[UUID]
    role_names: list[str]