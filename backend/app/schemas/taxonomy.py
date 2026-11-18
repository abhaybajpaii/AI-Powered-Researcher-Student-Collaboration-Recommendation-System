from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TopicSkillBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    slug: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., description="RESEARCH_TOPIC, METHODOLOGY, TECHNICAL_SKILL, or DOMAIN")
    parent_id: Optional[UUID] = None
    description: Optional[str] = None


class TopicSkillCreate(TopicSkillBase):
    pass


class TopicSkillResponse(TopicSkillBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class StudentSkillInterestCreate(BaseModel):
    topic_skill_id: UUID
    proficiency_level: int = Field(default=3, ge=1, le=5)
    interest_level: int = Field(default=5, ge=1, le=5)
    years_experience: Optional[float] = Field(default=1.0, ge=0.0)


class StudentSkillInterestResponse(StudentSkillInterestCreate):
    id: UUID
    topic_skill: Optional[TopicSkillResponse] = None

    model_config = ConfigDict(from_attributes=True)


class FacultySkillExpertiseCreate(BaseModel):
    topic_skill_id: UUID
    expertise_level: int = Field(default=5, ge=1, le=5)
    is_primary_focus: bool = False


class FacultySkillExpertiseResponse(FacultySkillExpertiseCreate):
    id: UUID
    topic_skill: Optional[TopicSkillResponse] = None

    model_config = ConfigDict(from_attributes=True)
