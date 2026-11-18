import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, JSON, TypeEngine


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> TypeEngine:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(str(value)))
            else:
                return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


class SafeVector(TypeDecorator):
    """Platform-independent Vector type.
    Uses pgvector's Vector type on PostgreSQL, otherwise falls back to JSON.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 384, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> TypeEngine:
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except ImportError:
                return dialect.type_descriptor(JSON)
        return dialect.type_descriptor(JSON)


class Base(DeclarativeBase):
    """Base model providing UUID primary key and timezone-aware timestamps."""
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
