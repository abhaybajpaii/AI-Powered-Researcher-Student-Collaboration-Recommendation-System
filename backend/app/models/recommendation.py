import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from backend.app.models.base import Base, GUID


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student", back_populates="recommendation_runs"
    )
    results: Mapped[List["RecommendationResult"]] = relationship(
        "RecommendationResult", back_populates="run", cascade="all, delete-orphan"
    )


class RecommendationResult(Base):
    __tablename__ = "recommendation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    semantic_score: Mapped[float] = mapped_column(Float, nullable=False)
    skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    project_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    user_interacted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feedback_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feedback_notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    run: Mapped["RecommendationRun"] = relationship(
        "RecommendationRun", back_populates="results"
    )
    faculty: Mapped["Faculty"] = relationship(
        "Faculty", back_populates="recommendation_results"
    )

    __table_args__ = (
        UniqueConstraint("run_id", "faculty_id", name="uq_run_faculty"),
    )
