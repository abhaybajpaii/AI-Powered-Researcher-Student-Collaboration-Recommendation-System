from backend.app.embeddings.service import EmbeddingService, embedding_service
from backend.app.embeddings.text_aggregator import (
    compose_faculty_profile_text,
    compose_project_text,
    compose_publication_text,
    compose_student_profile_text,
)

__all__ = [
    "EmbeddingService",
    "embedding_service",
    "compose_student_profile_text",
    "compose_faculty_profile_text",
    "compose_publication_text",
    "compose_project_text",
]
