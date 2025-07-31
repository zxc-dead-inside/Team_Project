from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, validator


class URLCreateRequest(BaseModel):
    url: HttpUrl = Field(..., description="The URL to shorten")
    custom_code: str | None = Field(None, description="Optional custom short code")
    expires_in_hours: int | None = Field(168, description="Hours until expiration (default 7 days)")
    
    @validator('custom_code')
    def validate_custom_code(cls, v):
        if v and (len(v) < 4 or len(v) > 10):
            raise ValueError('Custom code must be 4-10 characters')
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Custom code must be alphanumeric (with optional _ or -)')
        return v
    
    @validator('expires_in_hours')
    def validate_expiration(cls, v):
        if v and (v < 1 or v > 8760):  # Max 1 year
            raise ValueError('Expiration must be between 1 hour and 1 year')
        return v

class URLResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    expires_at: datetime | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class URLStats(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime
    is_active: bool
    expires_at: datetime | None = None
    
    class Config:
        from_attributes = True