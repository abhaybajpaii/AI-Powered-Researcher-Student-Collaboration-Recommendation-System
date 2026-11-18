import uuid
from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, GUID, TimestampMixin


class TopicSkill(Base):
    __tablename__ = "topics_and_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # RESEARCH_TOPIC, METHODOLOGY, TECHNICAL_SKILL, DOMAIN
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("topics_and_skills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    parent: Mapped[Optional["TopicSkill"]] = relationship(
        "TopicSkill", remote_side=[id], backref="children"
    )
    student_associations: Mapped[List["StudentSkillInterest"]] = relationship(
        "StudentSkillInterest", back_populates="topic_skill", cascade="all, delete-orphan"
    )
    faculty_associations: Mapped[List["FacultySkillExpertise"]] = relationship(
        "FacultySkillExpertise", back_populates="topic_skill", cascade="all, delete-orphan"
    )


class StudentSkillInterest(Base):
    __tablename__ = "student_skills_interests"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_skill_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("topics_and_skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proficiency_level: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False
    )  # 1 to 5
    interest_level: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False
    )  # 1 to 5
    years_experience: Mapped[Optional[float]] = mapped_column(Float, default=1.0)

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student", back_populates="skills_interests"
    )
    topic_skill: Mapped["TopicSkill"] = relationship(
        "TopicSkill", back_populates="student_associations", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("student_id", "topic_skill_id", name="uq_student_skill"),
    )


class FacultySkillExpertise(Base):
    __tablename__ = "faculty_skills_expertise"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_skill_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("topics_and_skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expertise_level: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False
    )  # 1 to 5
    is_primary_focus: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    faculty: Mapped["Faculty"] = relationship(
        "Faculty", back_populates="skills_expertise"
    )
    topic_skill: Mapped["TopicSkill"] = relationship(
        "TopicSkill", back_populates="faculty_associations", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("faculty_id", "topic_skill_id", name="uq_faculty_skill"),
    )
