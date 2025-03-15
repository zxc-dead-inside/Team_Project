"""Model for tracking system audit events."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.db.base_models import IdMixin, Base


class AuditLog(IdMixin, Base):
    """Model for tracking sensitive system operations."""

    __tablename__ = "audit_logs"

    actor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    timestamp = Column(
        DateTime(timezone=True), default=datetime.now(UTC), nullable=False, index=True
    )
    ip_address = Column(String(45), nullable=True)
    details = Column(JSON, nullable=True)

    actor = relationship("User", foreign_keys=[actor_id], backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.actor_id} at {self.timestamp}>"
