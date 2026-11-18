import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, GUID, TimestampMixin


class Faculty(Base, TimestampMixin):
    __tablename__ = "faculty"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True
    )
    faculty_number: Mapped[Optional[str]] = mapped_column(
        String(64), unique=True, nullable=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    title_rank: Mapped[str] = mapped_column(
        String(100), nullable=False, default="ASSISTANT_PROFESSOR"
    )  # ASSISTANT_PROFESSOR, ASSOCIATE_PROFESSOR, FULL_PROFESSOR, RESEARCH_SCIENTIST, EMERITUS
    office_location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    lab_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    accepting_students: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    max_capacity: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    current_student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Real vs. Synthetic Provenance & Verification (Phase 6)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), default="VERIFIED", nullable=False, index=True
    )  # UNVERIFIED, PENDING_REVIEW, VERIFIED, REJECTED_OUTDATED
    openalex_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    institution_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    institution_ror: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="faculty_profile")
    skills_expertise: Mapped[List["FacultySkillExpertise"]] = relationship(
        "FacultySkillExpertise", back_populates="faculty", cascade="all, delete-orphan"
    )
    authorship_links: Mapped[List["PublicationAuthorship"]] = relationship(
        "PublicationAuthorship", back_populates="faculty"
    )
    recommendation_results: Mapped[List["RecommendationResult"]] = relationship(
        "RecommendationResult", back_populates="faculty", cascade="all, delete-orphan"
    )
