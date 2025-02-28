from sqlalchemy import UUID, Column, ForeignKey, String
from sqlalchemy.orm import relationship
from src.db.base_models import Base, PreBase


class ContentRestriction(PreBase, Base):
    """Model for defining content access restrictions."""

    __tablename__ = "content_restrictions"

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    required_role_id = Column(UUID, ForeignKey("roles.id"), nullable=False)

    # Relationships
    required_role = relationship("Role")

    def __repr__(self):
        return f"<ContentRestriction {self.name}>"
