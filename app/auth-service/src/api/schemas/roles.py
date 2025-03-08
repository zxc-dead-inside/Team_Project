"""Pydantic schemas for role operations."""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PermissionBase(BaseModel):
    """Base schema for permission."""

    id: UUID
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base schema for role."""

    name: str = Field(..., min_length=3, max_length=50)
    description: str | None = Field(None, max_length=255)


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    permission_ids: list[UUID] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        """Validate that the role name is valid."""
        if not v.strip():
            raise ValueError("Role name cannot be empty")
        if not v.isalnum() and not all(c.isalnum() or c in ["_", "-"] for c in v):
            raise ValueError(
                "Role name must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v.lower()  # Normalize role names to lowercase


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    name: str | None = Field(None, min_length=3, max_length=50)
    description: str | None = Field(None, max_length=255)
    permission_ids: list[UUID] | None = None

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str | None) -> str | None:
        """Validate that the role name is valid."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError("Role name cannot be empty")
        if not v.isalnum() and not all(c.isalnum() or c in ["_", "-"] for c in v):
            raise ValueError(
                "Role name must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v.lower()  # Normalize role names to lowercase


class RoleResponse(RoleBase):
    """Schema for role response."""

    id: UUID
    permissions: list[PermissionBase] = Field(default_factory=list)

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """Schema for list of roles response."""

    roles: list[RoleResponse]
    total: int
