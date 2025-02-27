from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, String
from sqlalchemy.orm import relationship
from src.db.database import Base


class Permission(Base):
    """Permission model for granular access control."""

    __tablename__ = "permissions"

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC)
    )

    # Relationships
    roles = relationship(
        "Role", secondary="role_permission", back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission {self.name}>"
