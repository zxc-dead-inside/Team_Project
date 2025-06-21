from sqlalchemy import UUID, Column, ForeignKey, String
from sqlalchemy.orm import relationship

# from uuid import UUID
from src.db.base_models import Base, IdMixin


class OAuthAccount(IdMixin, Base):
    """Model for storing an OAuth2 accounts."""

    __tablename__ = "oauth_accounts"

    user_id = Column(UUID, ForeignKey("users.id"))
    provider = Column(String(50), primary_key=True)
    user = relationship("User", back_populates="oauth_accounts")
    provider_id = Column(String(255), primary_key=True)
