import re

from pydantic import BaseModel, Field, field_validator


class PermissionCreate(BaseModel):
    """Validation schema for permission creation."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)

    @field_validator("name")
    def name_format(cls, v):
        """Validate permission name format."""
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError("Permission name must be lowercase with no spaces")
        return v