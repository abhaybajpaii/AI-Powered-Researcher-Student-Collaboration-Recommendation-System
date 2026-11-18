from backend.app.models.base import Base, GUID, SafeVector, TimestampMixin
from backend.app.models.user import User
from backend.app.models.taxonomy import TopicSkill, StudentSkillInterest, FacultySkillExpertise
from backend.app.models.student import Student
from backend.app.models.faculty import Faculty
from backend.app.models.project import AcademicProject, project_skills
from backend.app.models.publication import Publication, PublicationAuthorship
from backend.app.models.embedding import EmbeddingRecord
from backend.app.models.recommendation import RecommendationRun, RecommendationResult
from backend.app.models.evaluation import RelevanceJudgment
from backend.app.models.provenance import DataSource, ImportJob, EntityProvenance

__all__ = [
    "Base",
    "GUID",
    "SafeVector",
    "TimestampMixin",
    "User",
    "TopicSkill",
    "StudentSkillInterest",
    "FacultySkillExpertise",
    "Student",
    "Faculty",
    "AcademicProject",
    "project_skills",
    "Publication",
    "PublicationAuthorship",
    "EmbeddingRecord",
    "RecommendationRun",
    "RecommendationResult",
    "RelevanceJudgment",
    "DataSource",
    "ImportJob",
    "EntityProvenance",
]
