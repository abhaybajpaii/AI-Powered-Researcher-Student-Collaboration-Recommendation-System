"""Tests for the scoring module: cosine similarity, skill compatibility,
publication aggregation, project similarity, and explanation generation.
"""

import uuid
import pytest
import numpy as np
from unittest.mock import MagicMock
from backend.app.recommendations.scoring import (
    aggregate_top_k_publications,
    compute_cosine_similarity,
    compute_project_similarity,
    compute_skill_compatibility,
    generate_explanation_summary,
)
from backend.app.recommendations.schemas import PublicationEvidence
from backend.app.recommendations.schemas import RecommendationWeights


class TestCosineSimilarity:
    def test_identical_vectors(self):
        vec = [0.5, 0.5, 0.5, 0.5]
        sim = compute_cosine_similarity(vec, vec)
        assert sim >= 0.99, f"Identical vectors should have similarity ~1.0, got {sim}"

    def test_orthogonal_vectors(self):
        v1 = [1.0, 0.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0, 0.0]
        sim = compute_cosine_similarity(v1, v2)
        assert sim == 0.0 or abs(sim) < 0.01

    def test_anti_correlated_vectors_have_zero_similarity(self):
        assert compute_cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == 0.0

    def test_none_vectors(self):
        assert compute_cosine_similarity(None, [1, 2, 3]) == 0.0
        assert compute_cosine_similarity([1, 2, 3], None) == 0.0
        assert compute_cosine_similarity(None, None) == 0.0

    def test_empty_vectors(self):
        assert compute_cosine_similarity([], []) == 0.0

    def test_bounded_output(self):
        """Similarity should always be in [0.0, 1.0]."""
        v1 = list(np.random.randn(384).astype(float))
        v2 = list(np.random.randn(384).astype(float))
        sim = compute_cosine_similarity(v1, v2)
        assert 0.0 <= sim <= 1.0, f"Similarity should be bounded [0,1], got {sim}"


class TestSkillCompatibility:
    def _make_skill(self, topic_id, topic_name, level_key, level_val):
        """Create a mock skill object."""
        mock = MagicMock()
        mock.topic_skill_id = topic_id
        mock.topic_skill = MagicMock()
        mock.topic_skill.name = topic_name
        setattr(mock, level_key, level_val)
        return mock

    def test_perfect_overlap(self):
        tid = uuid.uuid4()
        stu_skills = [self._make_skill(tid, "ML", "interest_level", 5)]
        fac_skills = [self._make_skill(tid, "ML", "expertise_level", 5)]
        score, shared = compute_skill_compatibility(stu_skills, fac_skills)
        assert score > 0.5
        assert "ML" in shared

    def test_no_overlap(self):
        stu_skills = [self._make_skill(uuid.uuid4(), "NLP", "interest_level", 5)]
        fac_skills = [self._make_skill(uuid.uuid4(), "CV", "expertise_level", 5)]
        score, shared = compute_skill_compatibility(stu_skills, fac_skills)
        assert len(shared) == 0
        assert score < 0.5

    def test_empty_skills(self):
        score, shared = compute_skill_compatibility([], [])
        assert score == 0.0
        assert shared == []

    def test_partial_overlap(self):
        tid1 = uuid.uuid4()
        tid2 = uuid.uuid4()
        tid3 = uuid.uuid4()
        stu = [
            self._make_skill(tid1, "ML", "interest_level", 4),
            self._make_skill(tid2, "CV", "interest_level", 3),
        ]
        fac = [
            self._make_skill(tid1, "ML", "expertise_level", 5),
            self._make_skill(tid3, "NLP", "expertise_level", 4),
        ]
        score, shared = compute_skill_compatibility(stu, fac)
        assert 0.0 < score < 1.0
        assert "ML" in shared
        assert "CV" not in shared

    def test_taxonomy_skill_score_matches_formula_and_dict_inputs(self):
        topic_id = uuid.uuid4()
        student = [
            {"topic_skill_id": topic_id, "topic_name": "Machine Learning", "interest_level": 4},
            {"topic_skill_id": uuid.uuid4(), "topic_name": "Vision", "interest_level": 3},
        ]
        faculty = [
            {"topic_skill_id": topic_id, "topic_name": "Machine Learning", "expertise_level": 5},
            {"topic_skill_id": uuid.uuid4(), "topic_name": "NLP", "expertise_level": 4},
        ]

        score, shared = compute_skill_compatibility(student, faculty)

        assert score == 0.5667
        assert shared == ["Machine Learning"]

class TestPublicationAggregation:
    def _make_pub(self, title, abstract="Test abstract content"):
        pub = MagicMock()
        pub.id = uuid.uuid4()
        pub.title = title
        pub.abstract = abstract
        pub.publication_year = 2024
        pub.venue = "NeurIPS"
        return pub

    def test_basic_aggregation(self):
        query_vec = list(np.random.randn(64).astype(float))
        pubs = [
            (self._make_pub("Paper 1"), list(np.random.randn(64).astype(float))),
            (self._make_pub("Paper 2"), list(np.random.randn(64).astype(float))),
            (self._make_pub("Paper 3"), list(np.random.randn(64).astype(float))),
        ]
        score, evidences = aggregate_top_k_publications(query_vec, pubs, top_k=3)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert len(evidences) <= 3
        for e in evidences:
            assert isinstance(e, PublicationEvidence)
            assert e.title in ["Paper 1", "Paper 2", "Paper 3"]

    def test_empty_publications(self):
        score, evidences = aggregate_top_k_publications([0.1, 0.2], [], top_k=3)
        assert score == 0.0
        assert evidences == []

    def test_no_query_vector(self):
        pub = self._make_pub("Test")
        score, evidences = aggregate_top_k_publications(None, [(pub, [0.1, 0.2])], top_k=3)
        assert score == 0.0

    def test_top_k_limits(self):
        query_vec = list(np.random.randn(64).astype(float))
        pubs = [
            (self._make_pub(f"Paper {i}"), list(np.random.randn(64).astype(float)))
            for i in range(10)
        ]
        _, evidences = aggregate_top_k_publications(query_vec, pubs, top_k=2)
        assert len(evidences) == 2

    def test_weighted_publication_aggregation_matches_hand_calculation(self):
        query = [1.0, 0.0]
        publications = [
            (self._make_pub("Exact"), [1.0, 0.0]),
            (self._make_pub("Close"), [0.8, 0.6]),
            (self._make_pub("Orthogonal"), [0.0, 1.0]),
        ]

        score, evidence = aggregate_top_k_publications(query, publications)

        assert score == 0.84
        assert [item.title for item in evidence] == ["Exact", "Close", "Orthogonal"]


class TestProjectSimilarity:
    def test_basic_similarity(self):
        proj_vec = list(np.random.randn(64).astype(float))
        pub_vec = list(np.random.randn(64).astype(float))
        proj = MagicMock()
        pub = MagicMock()
        score = compute_project_similarity(
            [(proj, proj_vec)],
            [(pub, pub_vec)],
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_no_projects(self):
        assert compute_project_similarity([], [(MagicMock(), [0.1])]) == 0.0

    def test_no_publications(self):
        assert compute_project_similarity([(MagicMock(), [0.1])], []) == 0.0

    def test_top_three_project_publication_aggregation_matches_formula(self):
        projects = [(MagicMock(), [1.0, 0.0]), (MagicMock(), [0.0, 1.0])]
        publications = [
            (MagicMock(), [1.0, 0.0]),
            (MagicMock(), [0.6, 0.8]),
        ]

        score = compute_project_similarity(projects, publications)

        assert score == 0.94


def test_recommendation_weight_normalization_boundaries():
    weights = RecommendationWeights()

    assert weights.normalized(["research_interest", "skill_compatibility"]) == {
        "research_interest": 0.8,
        "skill_compatibility": 0.2,
    }
    assert weights.normalized([]) == {}
    assert RecommendationWeights(
        research_interest=0,
        project_research=0,
        publication_relevance=0,
        skill_compatibility=0,
    ).normalized(["research_interest", "skill_compatibility"]) == {
        "research_interest": 0.5,
        "skill_compatibility": 0.5,
    }


class TestExplanationGeneration:
    def test_high_research_score(self):
        explanation = generate_explanation_summary(
            faculty_name="Dr. Smith",
            lab_name="AI Lab",
            research_score=0.85,
            skill_score=0.5,
            shared_skills=["ML", "NLP"],
            top_pubs=[
                PublicationEvidence(
                    publication_id=uuid.uuid4(),
                    title="Advanced NLP Methods",
                    year=2024,
                    venue="ACL",
                    similarity_score=0.88,
                    relevant_excerpt="We propose a novel method...",
                ),
            ],
            caveats=[],
        )
        assert "Dr. Smith" in explanation
        assert "strong" in explanation.lower() or "85%" in explanation
        assert "AI Lab" in explanation

    def test_low_research_score(self):
        explanation = generate_explanation_summary(
            faculty_name="Dr. Jones",
            lab_name=None,
            research_score=0.3,
            skill_score=0.2,
            shared_skills=[],
            top_pubs=[],
            caveats=["Limited data"],
        )
        assert "Dr. Jones" in explanation
        assert "cross-disciplinary" in explanation.lower() or "exploratory" in explanation.lower()

    def test_with_caveats(self):
        explanation = generate_explanation_summary(
            faculty_name="Dr. Lee",
            lab_name="Vision Lab",
            research_score=0.6,
            skill_score=0.4,
            shared_skills=["CV"],
            top_pubs=[],
            caveats=["Faculty has no publications indexed"],
        )
        assert "Note" in explanation
