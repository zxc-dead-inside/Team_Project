from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, ForeignKey, Index, String
from src.db.database import Base


class TokenBlacklist(Base):
    """Model for storing invalidated tokens."""

    __tablename__ = "token_blacklist"

    id = Column(UUID, primary_key=True, default=uuid4)
    token = Column(String(255), nullable=False, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    blacklisted_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    jti = Column(String(36), nullable=False, unique=True, index=True)  # JWT ID

    # Indexes for faster queries
    __table_args__ = (Index("ix_token_blacklist_token_jti", "token", "jti"),)

    def __repr__(self):
        return f"<TokenBlacklist {self.jti}>"
