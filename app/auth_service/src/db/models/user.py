"""User model for the database."""

from datetime import UTC, datetime

from sqlalchemy import (
    UUID, Boolean, Column, Date, DateTime, ForeignKey, String, Table
)
from sqlalchemy.orm import relationship
from src.db.base_models import Base, PreBase


# Association table for User-Role relationship
user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", UUID, ForeignKey("users.id"), primary_key=True),
    Column("role_id", UUID, ForeignKey("roles.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=datetime.now(UTC)),
)


class User(PreBase, Base):
    """User model for authentication."""

    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    phone_number = Column(String(15), unique=True, nullable=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    birth_date = Column(Date, nullable=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    token_version = Column(DateTime(timezone=True), nullable=True)

    # External OAuth
    oauth_accounts = relationship(
        "OAuthAccount", cascade="all, delete-orphan", back_populates="user"
    )

    # Relationships
    roles = relationship("Role", secondary=user_role, back_populates="users")
    login_history = relationship(
        "LoginHistory", back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions = relationship(
        "Subscription", back_populates="user", cascade="all, delete"
    )


    def __repr__(self):
        return f"<User {self.username}>"
