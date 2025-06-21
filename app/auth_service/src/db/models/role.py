from datetime import UTC, datetime

from sqlalchemy import UUID, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import relationship
from src.db.base_models import Base, PreBase


# Association table for Role-Permission relationship
role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", UUID, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", UUID, ForeignKey("permissions.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=datetime.now(UTC)),
)


class Role(PreBase, Base):
    """Role model for access control."""

    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    # Relationships
    users = relationship("User", secondary="user_role", back_populates="roles")
    permissions = relationship(
        "Permission", secondary=role_permission, back_populates="roles"
    )

    def __repr__(self):
        return f"<Role {self.name}>"
