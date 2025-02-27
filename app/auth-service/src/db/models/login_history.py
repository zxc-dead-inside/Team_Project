from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from src.db.database import Base


class LoginHistory(Base):
    """Model for tracking user login history."""

    __tablename__ = "login_history"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(
        String(45), nullable=True
    )  # IPv6 addresses can be up to 45 characters
    login_time = Column(DateTime(timezone=True), default=datetime.now(UTC), index=True)
    successful = Column(String(1), default="Y")  # Y/N flag

    # Relationships
    user = relationship("User", back_populates="login_history")

    def __repr__(self):
        return f"<LoginHistory {self.user_id} at {self.login_time}>"
