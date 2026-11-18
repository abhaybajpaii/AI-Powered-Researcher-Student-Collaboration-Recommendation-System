from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.taxonomy import FacultySkillExpertiseResponse


class FacultyBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=2, max_length=150)
    title_rank: str = Field(
        default="ASSISTANT_PROFESSOR",
        description="ASSISTANT_PROFESSOR, ASSOCIATE_PROFESSOR, FULL_PROFESSOR, RESEARCH_SCIENTIST, EMERITUS",
    )
    office_location: Optional[str] = None
    website_url: Optional[str] = None
    lab_name: Optional[str] = None
    accepting_students: bool = True
    max_capacity: int = Field(default=5, ge=0)
    current_student_count: int = Field(default=0, ge=0)
    bio: Optional[str] = None
    is_synthetic: bool = True
    verification_status: str = Field(
        default="VERIFIED",
        description="UNVERIFIED, PENDING_REVIEW, VERIFIED, or REJECTED_OUTDATED",
    )
    openalex_id: Optional[str] = None
    institution_name: Optional[str] = None
    institution_ror: Optional[str] = None
    verification_notes: Optional[str] = None
    verified_at: Optional[datetime] = None


class FacultyCreate(FacultyBase):
    user_id: Optional[UUID] = None
    faculty_number: Optional[str] = None


class FacultyUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    department: Optional[str] = Field(default=None, min_length=2, max_length=150)
    title_rank: Optional[str] = None
    office_location: Optional[str] = None
    website_url: Optional[str] = None
    lab_name: Optional[str] = None
    accepting_students: Optional[bool] = None
    max_capacity: Optional[int] = Field(default=None, ge=0)
    current_student_count: Optional[int] = Field(default=None, ge=0)
    bio: Optional[str] = None
    verification_status: Optional[str] = None
    verification_notes: Optional[str] = None
    institution_name: Optional[str] = None
    institution_ror: Optional[str] = None


class FacultyResponse(FacultyBase):
    id: UUID
    user_id: Optional[UUID] = None
    faculty_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationAuthorshipPublicationResponse(BaseModel):
    id: UUID
    title: str
    abstract: Optional[str] = None
    venue: Optional[str] = None
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    citation_count: int = 0
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PublicationAuthorshipResponse(BaseModel):
    id: UUID
    publication_id: UUID
    faculty_id: Optional[UUID] = None
    author_order: int = 1
    raw_author_name: str
    is_corresponding: bool = False
    publication: Optional[PublicationAuthorshipPublicationResponse] = None

    model_config = ConfigDict(from_attributes=True)


class FacultyDetailResponse(FacultyResponse):
    skills_expertise: List[FacultySkillExpertiseResponse] = Field(default_factory=list)
    authorship_links: List[PublicationAuthorshipResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
