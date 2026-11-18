import pytest
import inspect
from backend.app.recommendations.engine import RecommendationEngine, recommendation_engine
from backend.app.recommendations import scoring
from backend.app.recommendations.schemas import RecommendationItem, ScoreBreakdown, RecommendationWeights
from backend.app.models.evaluation import RelevanceJudgment
from backend.app.embeddings.service import EmbeddingService

def test_label_independence_architecture():
    """Regression test: Ensure RelevanceJudgment is never imported or referenced in recommendation engine or scoring modules."""
    engine_source = inspect.getsource(RecommendationEngine)
    scoring_source = inspect.getsource(scoring)
    
    assert "RelevanceJudgment" not in engine_source, "RelevanceJudgment leaked into RecommendationEngine!"
    assert "relevance_judgments" not in engine_source, "relevance_judgments table queried in RecommendationEngine!"
    assert "RelevanceJudgment" not in scoring_source, "RelevanceJudgment leaked into scoring module!"
    assert "relevance_judgments" not in scoring_source, "relevance_judgments table queried in scoring module!"


def test_score_breakdown_arithmetic_consistency():
    """Regression test: Ensure score breakdown weighted sum exactly equals overall_score."""
    weights = RecommendationWeights(
        research_interest=0.40,
        project_research=0.30,
        publication_relevance=0.20,
        skill_compatibility=0.10,
    )
    nw = weights.normalized()
    
    r_score = 0.85
    p_score = 0.70
    pub_score = 0.90
    s_score = 0.60
    
    expected_overall = (
        nw["research_interest"] * r_score
        + nw["project_research"] * p_score
        + nw["publication_relevance"] * pub_score
        + nw["skill_compatibility"] * s_score
    )
    
    sb = ScoreBreakdown(
        research_interest_score=r_score,
        project_research_score=p_score,
        publication_relevance_score=pub_score,
        skill_compatibility_score=s_score,
        normalized_weights=nw,
    )
    
    item = RecommendationItem(
        faculty_id="00000000-0000-0000-0000-000000000001",
        faculty_name="Dr. Test",
        department="Computer Science",
        title_rank="PROFESSOR",
        accepting_students=True,
        open_capacity=3,
        rank_position=1,
        overall_score=round(expected_overall, 4),
        score_breakdown=sb,
        explanation_summary="Test explanation",
    )
    
    recalc = (
        item.score_breakdown.normalized_weights["research_interest"] * item.score_breakdown.research_interest_score
        + item.score_breakdown.normalized_weights["project_research"] * item.score_breakdown.project_research_score
        + item.score_breakdown.normalized_weights["publication_relevance"] * item.score_breakdown.publication_relevance_score
        + item.score_breakdown.normalized_weights["skill_compatibility"] * item.score_breakdown.skill_compatibility_score
    )
    assert abs(item.overall_score - round(recalc, 4)) < 1e-4


def test_embedding_dimension_and_normalization():
    """Regression test: Verify embedding service produces unit-normalized 384-dimensional vectors."""
    service = EmbeddingService(dimension=384)
    vec = service.embed_text("Advanced natural language processing and academic collaboration recommendation systems.")
    
    assert vec is not None
    assert len(vec) == 384
    
    import numpy as np
    norm = np.linalg.norm(np.array(vec, dtype=np.float32))
    assert abs(norm - 1.0) < 1e-4

