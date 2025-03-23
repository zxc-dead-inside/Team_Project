"""Base models and mixins for SQLAlchemy models."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class IdMixin:
    """Mixin that provides just the UUID primary key."""

    @declared_attr
    def id(cls):  # noqa: N805
        return Column(UUID, primary_key=True, default=uuid4)


class TimestampMixin:
    """Mixin that provides created_at and updated_at timestamp fields."""

    @declared_attr
    def created_at(cls):  # noqa: N805
        return Column(DateTime(timezone=True), default=datetime.now(UTC))

    @declared_attr
    def updated_at(cls):  # noqa: N805
        return Column(
            DateTime(timezone=True),
            default=datetime.now(UTC),
            onupdate=datetime.now(UTC),
        )


class PreBase(IdMixin, TimestampMixin):
    """Mixin class that provides common columns and functionality for models.

    Includes:
    - UUID primary key
    - created_at timestamp
    - updated_at timestamp
    """

    pass