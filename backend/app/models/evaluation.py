import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, GUID


class RelevanceJudgment(Base):
    __tablename__ = "relevance_judgments"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False, index=True
    )
    benchmark_suite: Mapped[str] = mapped_column(
        String(100), default="standard_eval_v1", nullable=False, index=True
    )
    relevance_grade: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 0=Irrelevant, 1=Marginal, 2=Relevant, 3=Highly Relevant
    annotator_id: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student")
    faculty: Mapped["Faculty"] = relationship("Faculty")

    __table_args__ = (
        UniqueConstraint(
            "student_id", "faculty_id", "benchmark_suite", name="uq_student_faculty_suite"
        ),
    )
