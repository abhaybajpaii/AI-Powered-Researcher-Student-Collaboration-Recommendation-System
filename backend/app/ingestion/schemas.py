from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from backend.app.ingestion.preprocessing import (
    generate_title_hash,
    normalize_doi,
    normalize_text,
    slugify,
)


class TopicSkillIngestDTO(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., description="RESEARCH_TOPIC, METHODOLOGY, TECHNICAL_SKILL, or DOMAIN")
    parent_slug: Optional[str] = None
    description: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return normalize_text(v)

    @property
    def slug(self) -> str:
        return slugify(self.name)


class StudentSkillIngestDTO(BaseModel):
    topic_slug: str
    proficiency_level: int = Field(default=3, ge=1, le=5)
    interest_level: int = Field(default=5, ge=1, le=5)
    years_experience: Optional[float] = Field(default=1.0, ge=0.0)


class ProjectIngestDTO(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=10)
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    github_url: Optional[str] = None
    skill_slugs: List[str] = Field(default_factory=list)

    @field_validator("title", "description", mode="before")
    @classmethod
    def clean_text(cls, v: str) -> str:
        return normalize_text(v)


class StudentIngestDTO(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=2, max_length=150)
    degree_level: str = Field(default="UNDERGRADUATE")
    gpa_or_standing: Optional[float] = Field(default=None, ge=0.0, le=4.0)
    graduation_year: Optional[int] = Field(default=None, ge=2000, le=2100)
    bio: Optional[str] = None
    statement_of_purpose: str = Field(..., min_length=10)
    availability_status: str = Field(default="SEEKING_ADVISOR")
    skills: List[StudentSkillIngestDTO] = Field(default_factory=list)
    projects: List[ProjectIngestDTO] = Field(default_factory=list)

    @field_validator("first_name", "last_name", "department", "statement_of_purpose", mode="before")
    @classmethod
    def clean_strings(cls, v: str) -> str:
        return normalize_text(v)


class FacultySkillIngestDTO(BaseModel):
    topic_slug: str
    expertise_level: int = Field(default=5, ge=1, le=5)
    is_primary_focus: bool = False


class FacultyIngestDTO(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=2, max_length=150)
    title_rank: str = Field(default="ASSISTANT_PROFESSOR")
    office_location: Optional[str] = None
    website_url: Optional[str] = None
    lab_name: Optional[str] = None
    accepting_students: bool = True
    max_capacity: int = Field(default=5, ge=0)
    current_student_count: int = Field(default=0, ge=0)
    bio: Optional[str] = None
    is_synthetic: bool = True
    verification_status: str = "VERIFIED"
    openalex_id: Optional[str] = None
    institution_name: Optional[str] = None
    institution_ror: Optional[str] = None
    verification_notes: Optional[str] = None
    skills: List[FacultySkillIngestDTO] = Field(default_factory=list)

    @field_validator("first_name", "last_name", "department", mode="before")
    @classmethod
    def clean_strings(cls, v: str) -> str:
        return normalize_text(v)


class PublicationIngestDTO(BaseModel):
    title: str = Field(..., min_length=3, max_length=512)
    abstract: str = Field(..., min_length=10)
    venue: Optional[str] = None
    publication_year: Optional[int] = Field(default=None, ge=1900, le=2100)
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    citation_count: int = Field(default=0, ge=0)
    url: Optional[str] = None
    is_synthetic: bool = True
    openalex_id: Optional[str] = None
    crossref_id: Optional[str] = None
    is_retracted: bool = False
    author_names: List[str] = Field(default_factory=list)
    author_faculty_emails: List[str] = Field(default_factory=list)
    topic_slugs: List[str] = Field(default_factory=list)

    @field_validator("title", "abstract", mode="before")
    @classmethod
    def clean_title_abstract(cls, v: str) -> str:
        return normalize_text(v)

    @field_validator("doi", mode="before")
    @classmethod
    def clean_doi(cls, v: Optional[str]) -> Optional[str]:
        return normalize_doi(v)

    @property
    def title_hash(self) -> str:
        return generate_title_hash(self.title, self.publication_year)


class RelevanceJudgmentIngestDTO(BaseModel):
    student_email: str
    faculty_email: str
    relevance_grade: int = Field(..., ge=0, le=3)
    benchmark_suite: str = "standard_eval_v1"
    annotator_id: str = "synthetic_annotator"
    notes: Optional[str] = None


class BatchIngestPayload(BaseModel):
    topics: List[TopicSkillIngestDTO] = Field(default_factory=list)
    faculty: List[FacultyIngestDTO] = Field(default_factory=list)
    students: List[StudentIngestDTO] = Field(default_factory=list)
    publications: List[PublicationIngestDTO] = Field(default_factory=list)
    relevance_judgments: List[RelevanceJudgmentIngestDTO] = Field(default_factory=list)
