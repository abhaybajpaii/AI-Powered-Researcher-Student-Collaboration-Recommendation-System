import uuid
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, GUID, TimestampMixin


class Publication(Base, TimestampMixin):
    __tablename__ = "publications"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    venue: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True
    )
    doi: Mapped[Optional[str]] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    pmid: Mapped[Optional[str]] = mapped_column(
        String(64), unique=True, nullable=True
    )
    arxiv_id: Mapped[Optional[str]] = mapped_column(
        String(64), unique=True, nullable=True
    )
    title_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    citation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Real vs. Synthetic Provenance & Identifiers (Phase 6)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    openalex_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    crossref_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_retracted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    authorships: Mapped[List["PublicationAuthorship"]] = relationship(
        "PublicationAuthorship", back_populates="publication", cascade="all, delete-orphan"
    )


class PublicationAuthorship(Base):
    __tablename__ = "publication_authorship"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    publication_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("publications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    faculty_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True, index=True
    )
    author_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    raw_author_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_corresponding: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    publication: Mapped["Publication"] = relationship(
        "Publication", back_populates="authorships"
    )
    faculty: Mapped[Optional["Faculty"]] = relationship(
        "Faculty", back_populates="authorship_links"
    )

    __table_args__ = (
        UniqueConstraint("publication_id", "faculty_id", name="uq_publication_faculty"),
    )
