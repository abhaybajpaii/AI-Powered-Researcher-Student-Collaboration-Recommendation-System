from backend.app.ingestion.preprocessing import (
    normalize_text,
    normalize_doi,
    generate_title_hash,
    slugify,
)
from backend.app.ingestion.schemas import (
    TopicSkillIngestDTO,
    StudentSkillIngestDTO,
    ProjectIngestDTO,
    StudentIngestDTO,
    FacultySkillIngestDTO,
    FacultyIngestDTO,
    PublicationIngestDTO,
    RelevanceJudgmentIngestDTO,
    BatchIngestPayload,
)
from backend.app.ingestion.deduplication import (
    find_existing_publication,
    find_existing_topic,
    find_existing_user,
)
from backend.app.ingestion.pipeline import ingestion_pipeline, IngestionPipeline

__all__ = [
    "normalize_text",
    "normalize_doi",
    "generate_title_hash",
    "slugify",
    "TopicSkillIngestDTO",
    "StudentSkillIngestDTO",
    "ProjectIngestDTO",
    "StudentIngestDTO",
    "FacultySkillIngestDTO",
    "FacultyIngestDTO",
    "PublicationIngestDTO",
    "RelevanceJudgmentIngestDTO",
    "BatchIngestPayload",
    "find_existing_publication",
    "find_existing_topic",
    "find_existing_user",
    "ingestion_pipeline",
    "IngestionPipeline",
]
