import uuid
from datetime import date
from typing import List, Optional
from sqlalchemy import Column, Date, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, GUID, TimestampMixin

# Many-to-many junction table between AcademicProject and TopicSkill
project_skills = Table(
    "project_skills",
    Base.metadata,
    Column(
        "project_id",
        GUID(),
        ForeignKey("academic_projects.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topic_skill_id",
        GUID(),
        ForeignKey("topics_and_skills.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class AcademicProject(Base):
    __tablename__ = "academic_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student", back_populates="academic_projects"
    )
    skills: Mapped[List["TopicSkill"]] = relationship(
        "TopicSkill", secondary=project_skills
    )
