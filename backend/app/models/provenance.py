import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from backend.app.models.base import Base, GUID, TimestampMixin


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # SYNTHETIC, OPENALEX, SEMANTIC_SCHOLAR, INSTITUTIONAL_CSV, MANUAL
    base_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    import_jobs: Mapped[List["ImportJob"]] = relationship(
        "ImportJob", back_populates="data_source", cascade="all, delete-orphan"
    )


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False
    )  # PENDING, RUNNING, COMPLETED, FAILED
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_log: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    data_source: Mapped["DataSource"] = relationship(
        "DataSource", back_populates="import_jobs"
    )
    provenance_records: Mapped[List["EntityProvenance"]] = relationship(
        "EntityProvenance", back_populates="import_job", cascade="all, delete-orphan"
    )


class EntityProvenance(Base):
    __tablename__ = "entity_provenance"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # STUDENT, FACULTY, PUBLICATION, TOPIC
    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), nullable=False, index=True
    )
    import_job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    import_job: Mapped["ImportJob"] = relationship(
        "ImportJob", back_populates="provenance_records"
    )

    __table_args__ = (
        UniqueConstraint(
            "entity_type", "entity_id", "import_job_id", name="uq_entity_provenance"
        ),
    )
