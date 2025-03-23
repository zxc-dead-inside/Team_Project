from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from testdata.base_models import Base, PreBase


class Permission(PreBase, Base):
    """Permission model for granular access control."""

    __tablename__ = "permissions"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    # Relationships
    roles = relationship(
        "Role", secondary="role_permission", back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission {self.name}>"
