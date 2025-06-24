from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base schema for user data."""

    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr


class UserProfile(UserBase):
    """Schema for user profile response."""

    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsernameUpdate(BaseModel):
    """Schema for username update request."""

    username: Annotated[str, Field(min_length=3, max_length=50)]

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate that username contains only valid characters."""
        if not v.isalnum() and not set(v).issubset(set("_-.")):
            raise ValueError(
                "Username must contain only alphanumeric characters, underscores, hyphens, or dots"
            )
        return v


class PasswordUpdate(BaseModel):
    """Schema for password update request."""

    current_password: Annotated[str, Field(min_length=1)]
    new_password: Annotated[str, Field(min_length=8, max_length=100)]

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginHistoryItem(BaseModel):
    """Schema for login history item response."""

    id: UUID
    user_agent: str | None = None
    ip_address: str | None = None
    login_time: datetime
    successful: Literal["Y", "N"]

    model_config = ConfigDict(from_attributes=True)


class LoginHistoryResponse(BaseModel):
    """Schema for paginated login history response."""

    items: list[LoginHistoryItem]
    total: int
    page: int
    size: int
    pages: int
