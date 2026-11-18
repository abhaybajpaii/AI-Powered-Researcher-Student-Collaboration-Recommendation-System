import uuid
from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, GUID, TimestampMixin


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    student_number: Mapped[Optional[str]] = mapped_column(
        String(64), unique=True, nullable=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    degree_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UNDERGRADUATE", index=True
    )  # UNDERGRADUATE, MASTERS, PHD
    gpa_or_standing: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    statement_of_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    availability_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="SEEKING_ADVISOR", index=True
    )  # SEEKING_ADVISOR, OPEN_TO_PROJECTS, NOT_AVAILABLE

    # Real vs. Synthetic flag
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="student_profile")
    skills_interests: Mapped[List["StudentSkillInterest"]] = relationship(
        "StudentSkillInterest", back_populates="student", cascade="all, delete-orphan"
    )
    academic_projects: Mapped[List["AcademicProject"]] = relationship(
        "AcademicProject", back_populates="student", cascade="all, delete-orphan"
    )
    recommendation_runs: Mapped[List["RecommendationRun"]] = relationship(
        "RecommendationRun", back_populates="student", cascade="all, delete-orphan"
    )
