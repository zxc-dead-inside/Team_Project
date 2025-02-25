"""User model for the database."""

from datetime import UTC, datetime
from enum import Enum

import sqlalchemy as sa
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Mapped, mapped_column
from src.db.database import Base


class UserRole(str, Enum):
    """User role enumeration."""
    
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User model for SQLAlchemy."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(sa.String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(sa.String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(sa.String(255))
    full_name: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    role: Mapped[str] = mapped_column(
        sa.String(10), default=UserRole.USER.value, index=True
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=datetime.now(UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC)
    )


class UserCreate(BaseModel):
    """Schema for user creation."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserResponse(BaseModel):
    """Schema for user response."""
    
    id: int
    username: str
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"