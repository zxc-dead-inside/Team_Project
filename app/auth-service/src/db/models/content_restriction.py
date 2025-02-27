from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from src.db.database import Base


class ContentRestriction(Base):
    """Model for defining content access restrictions."""

    __tablename__ = "content_restrictions"

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    required_role_id = Column(UUID, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC)
    )

    # Relationships
    required_role = relationship("Role")

    def __repr__(self):
        return f"<ContentRestriction {self.name}>"
