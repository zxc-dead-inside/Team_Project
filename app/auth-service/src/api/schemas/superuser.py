"""Schemas for superuser API endpoints."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SuperuserResponse(BaseModel):
    """Response model for superuser operations."""
    message: str


class SuperuserUserResponse(BaseModel):
    """Response model for superuser user details."""
    id: UUID
    username: str
    email: EmailStr
    roles: list[str] = Field(default_factory=list)


class SuperuserListResponse(BaseModel):
    """Response model for listing superusers."""
    superusers: list[SuperuserUserResponse]
    total: int


class AuditLogEntry(BaseModel):
    """Response model for an audit log entry."""
    id: UUID
    action: str
    actor_id: UUID | None = None
    actor_username: str | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    timestamp: str
    ip_address: str | None = None
    details: dict = Field(default_factory=dict)


class AuditLogResponse(BaseModel):
    """Response model for audit log listing."""
    logs: list[AuditLogEntry]
    total: int
    page: int
    size: int