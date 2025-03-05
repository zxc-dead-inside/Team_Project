import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base schema for User information."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False

    @field_validator("username")
    def username_alphanumeric(cls, v):
        """Validate username contains only alphanumeric characters and underscores."""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username must contain only letters, numbers, and underscores"
            )
        return v


class UserCreate(UserBase):
    """Schema for creating a User."""

    password: str = Field(..., min_length=8)
    role_ids: list[UUID] | None = []

    @field_validator("password")
    def password_strength(cls, v):
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserRead(UserBase):
    """Schema for reading User information."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailConfirmation(BaseModel):
    """Email confirmation schema."""

    token: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    username: str
    email: EmailStr
    is_active: bool

    class Config:
        """Pydantic config."""

        from_attributes = True
