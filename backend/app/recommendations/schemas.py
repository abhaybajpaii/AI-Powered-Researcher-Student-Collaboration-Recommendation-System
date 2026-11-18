from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class RecommendationWeights(BaseModel):
    research_interest: float = Field(default=0.40, ge=0.0, le=1.0)
    project_research: float = Field(default=0.30, ge=0.0, le=1.0)
    publication_relevance: float = Field(default=0.20, ge=0.0, le=1.0)
    skill_compatibility: float = Field(default=0.10, ge=0.0, le=1.0)

    def normalized(self, active_signals: Optional[List[str]] = None) -> Dict[str, float]:
        signals = active_signals if active_signals is not None else [
            "research_interest",
            "project_research",
            "publication_relevance",
            "skill_compatibility",
        ]
        if not signals:
            return {}
        total = sum(getattr(self, s, 0.0) for s in signals)
        if total <= 1e-6:
            return {s: 1.0 / len(signals) for s in signals}
        return {s: getattr(self, s) / total for s in signals}


class RecommendationFilters(BaseModel):
    departments: Optional[List[str]] = None
    only_accepting_students: bool = False
    min_capacity: Optional[int] = Field(default=None, ge=1)
    data_mode: str = Field(
        default="ALL",
        description="Operating mode: 'ALL', 'REAL_ONLY' (imported research data), or 'SYNTHETIC_ONLY' (demo data)",
    )
    verified_only: bool = Field(
        default=False,
        description="If True, only recommends faculty with verification_status == 'VERIFIED'",
    )


class RecommendationRequest(BaseModel):
    student_id: UUID
    top_k: int = Field(default=10, ge=1, le=50)
    weights: Optional[RecommendationWeights] = Field(default_factory=RecommendationWeights)
    filters: Optional[RecommendationFilters] = Field(default_factory=RecommendationFilters)


class PublicationEvidence(BaseModel):
    publication_id: UUID
    title: str
    year: Optional[int] = None
    venue: Optional[str] = None
    similarity_score: float
    relevant_excerpt: str


class ScoreBreakdown(BaseModel):
    research_interest_score: float
    project_research_score: float
    publication_relevance_score: float
    skill_compatibility_score: float
    normalized_weights: Dict[str, float]


class RecommendationItem(BaseModel):
    faculty_id: UUID
    faculty_name: str
    department: str
    title_rank: str
    lab_name: Optional[str] = None
    accepting_students: bool
    open_capacity: int
    rank_position: int
    overall_score: float
    score_breakdown: ScoreBreakdown
    top_publications: List[PublicationEvidence] = Field(default_factory=list)
    shared_skills: List[str] = Field(default_factory=list)
    explanation_summary: str
    missing_data_caveats: List[str] = Field(default_factory=list)
    is_synthetic: bool = True
    verification_status: str = "VERIFIED"
    openalex_id: Optional[str] = None
    institution_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    run_id: UUID
    student_id: UUID
    algorithm_version: str
    execution_time_ms: float
    total_candidates_evaluated: int
    recommendations: List[RecommendationItem]

    model_config = ConfigDict(from_attributes=True)
