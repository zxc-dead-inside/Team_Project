from sqlalchemy import BigInteger, Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


Base = declarative_base()

class URL(Base):
    __tablename__ = "urls"
    
    id = Column(BigInteger, primary_key=True, index=True)
    short_code = Column(String(10), unique=True, index=True, nullable=False)
    original_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    created_by_user_id = Column(BigInteger, nullable=True)
    is_active = Column(Boolean, default=True)
    click_count = Column(Integer, default=0)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_urls_short_code_active', 'short_code', 'is_active'),
        Index('idx_urls_created_at', 'created_at'),
        Index('idx_urls_expires_at', 'expires_at'),
    )

class URLClick(Base):
    __tablename__ = "url_clicks"
    
    id = Column(BigInteger, primary_key=True, index=True)
    url_id = Column(BigInteger, nullable=False, index=True)
    clicked_at = Column(DateTime, default=func.now())
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    referer = Column(Text)
    
    __table_args__ = (
        Index('idx_url_clicks_url_id_clicked_at', 'url_id', 'clicked_at'),
    )