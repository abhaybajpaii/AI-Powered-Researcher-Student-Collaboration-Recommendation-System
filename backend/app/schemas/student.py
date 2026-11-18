from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.taxonomy import StudentSkillInterestResponse


class StudentBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=2, max_length=150)
    degree_level: str = Field(
        default="UNDERGRADUATE",
        description="UNDERGRADUATE, MASTERS, or PHD",
    )
    gpa_or_standing: Optional[float] = Field(default=None, ge=0.0, le=4.0)
    graduation_year: Optional[int] = Field(default=None, ge=2000, le=2100)
    bio: Optional[str] = None
    statement_of_purpose: str = Field(..., min_length=10)
    availability_status: str = Field(
        default="SEEKING_ADVISOR",
        description="SEEKING_ADVISOR, OPEN_TO_PROJECTS, or NOT_AVAILABLE",
    )


class StudentCreate(StudentBase):
    user_id: UUID
    student_number: Optional[str] = None


class StudentUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    department: Optional[str] = Field(default=None, min_length=2, max_length=150)
    degree_level: Optional[str] = None
    gpa_or_standing: Optional[float] = Field(default=None, ge=0.0, le=4.0)
    graduation_year: Optional[int] = Field(default=None, ge=2000, le=2100)
    bio: Optional[str] = None
    statement_of_purpose: Optional[str] = Field(default=None, min_length=10)
    availability_status: Optional[str] = None


class AcademicProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=5)
    role: Optional[str] = Field(default=None, max_length=100)
    github_url: Optional[str] = Field(default=None, max_length=512)


class AcademicProjectCreate(AcademicProjectBase):
    pass


class AcademicProjectResponse(AcademicProjectBase):
    id: UUID
    student_id: UUID

    model_config = ConfigDict(from_attributes=True)


class StudentResponse(StudentBase):
    id: UUID
    user_id: UUID
    student_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentDetailResponse(StudentResponse):
    skills_interests: List[StudentSkillInterestResponse] = Field(default_factory=list)
    academic_projects: List[AcademicProjectResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

