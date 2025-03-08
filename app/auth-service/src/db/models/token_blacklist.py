from datetime import UTC, datetime

from sqlalchemy import UUID, Column, DateTime, ForeignKey, Index, String
from src.db.base_models import Base, IdMixin


class TokenBlacklist(IdMixin, Base):
    """Model for storing invalidated tokens."""

    __tablename__ = "token_blacklist"

    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    blacklisted_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    jti = Column(String(36), nullable=False, unique=True, index=True)  # JWT ID

    # Indexes for faster queries
    __table_args__ = (Index("ix_token_blacklist_token_jti", "jti"),)

    def __repr__(self):
        return f"<TokenBlacklist {self.jti}>"
