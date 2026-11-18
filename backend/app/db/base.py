# Import all models here so that Alembic detects them on Base.metadata
from backend.app.models.base import Base
from backend.app.models import (
    User,
    TopicSkill,
    StudentSkillInterest,
    FacultySkillExpertise,
    Student,
    Faculty,
    AcademicProject,
    project_skills,
    Publication,
    PublicationAuthorship,
    EmbeddingRecord,
    RecommendationRun,
    RecommendationResult,
    RelevanceJudgment,
    DataSource,
    ImportJob,
    EntityProvenance,
)

__all__ = ["Base"]
