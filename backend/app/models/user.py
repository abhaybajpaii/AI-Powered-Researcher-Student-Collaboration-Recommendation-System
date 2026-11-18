import uuid
from typing import Optional
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, GUID, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="STUDENT", index=True
    )  # STUDENT, FACULTY, ADMIN
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    student_profile: Mapped[Optional["Student"]] = relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    faculty_profile: Mapped[Optional["Faculty"]] = relationship(
        "Faculty", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
