from backend.app.recommendations.engine import RecommendationEngine, recommendation_engine
from backend.app.recommendations.schemas import (
    PublicationEvidence,
    RecommendationFilters,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationWeights,
    ScoreBreakdown,
)
from backend.app.recommendations.scoring import (
    aggregate_top_k_publications,
    compute_cosine_similarity,
    compute_project_similarity,
    compute_skill_compatibility,
    generate_explanation_summary,
)

__all__ = [
    "RecommendationEngine",
    "recommendation_engine",
    "RecommendationRequest",
    "RecommendationResponse",
    "RecommendationWeights",
    "RecommendationFilters",
    "RecommendationItem",
    "PublicationEvidence",
    "ScoreBreakdown",
    "compute_cosine_similarity",
    "compute_skill_compatibility",
    "aggregate_top_k_publications",
    "compute_project_similarity",
    "generate_explanation_summary",
]
