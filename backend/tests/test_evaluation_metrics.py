"""Tests for the evaluation metrics module: Precision@K, Recall@K, NDCG@K, MRR."""

import uuid
import pytest
from backend.app.evaluation.metrics import (
    dcg_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class TestPrecisionAtK:
    def test_perfect_precision(self):
        ids = [uuid.uuid4() for _ in range(5)]
        relevant = set(ids[:3])
        assert precision_at_k(ids[:3], relevant, 3) == 1.0

    def test_zero_precision(self):
        recommended = [uuid.uuid4() for _ in range(5)]
        relevant = {uuid.uuid4()}  # None of the recommended are relevant
        assert precision_at_k(recommended, relevant, 5) == 0.0

    def test_partial_precision(self):
        ids = [uuid.uuid4() for _ in range(4)]
        relevant = {ids[0], ids[2]}  # 2 out of 4
        assert precision_at_k(ids, relevant, 4) == 0.5

    def test_k_larger_than_list(self):
        ids = [uuid.uuid4()]
        relevant = {ids[0]}
        # K=5 but only 1 item — precision@5 = 1/5 = 0.2
        assert precision_at_k(ids, relevant, 5) == 0.2

    def test_empty_inputs(self):
        assert precision_at_k([], set(), 5) == 0.0
        assert precision_at_k([], {uuid.uuid4()}, 3) == 0.0
        assert precision_at_k([uuid.uuid4()], set(), 0) == 0.0


class TestRecallAtK:
    def test_perfect_recall(self):
        ids = [uuid.uuid4() for _ in range(5)]
        relevant = {ids[0], ids[1]}
        assert recall_at_k(ids, relevant, 5) == 1.0

    def test_zero_recall(self):
        recommended = [uuid.uuid4() for _ in range(5)]
        relevant = {uuid.uuid4()}
        assert recall_at_k(recommended, relevant, 5) == 0.0

    def test_partial_recall(self):
        ids = [uuid.uuid4() for _ in range(4)]
        relevant = {ids[0], ids[1], uuid.uuid4(), uuid.uuid4()}
        # 2 out of 4 relevant found
        assert recall_at_k(ids, relevant, 4) == 0.5

    def test_empty_relevant(self):
        assert recall_at_k([uuid.uuid4()], set(), 3) == 0.0


class TestReciprocalRank:
    def test_first_position(self):
        ids = [uuid.uuid4() for _ in range(5)]
        relevant = {ids[0]}
        assert reciprocal_rank(ids, relevant) == 1.0

    def test_second_position(self):
        ids = [uuid.uuid4() for _ in range(5)]
        relevant = {ids[1]}
        assert reciprocal_rank(ids, relevant) == 0.5

    def test_no_relevant(self):
        ids = [uuid.uuid4() for _ in range(5)]
        relevant = {uuid.uuid4()}
        assert reciprocal_rank(ids, relevant) == 0.0


class TestNDCG:
    def test_perfect_ranking(self):
        """When recommended order matches ideal order, NDCG should be 1.0."""
        ids = [uuid.uuid4() for _ in range(3)]
        grades = {ids[0]: 3, ids[1]: 2, ids[2]: 1}
        ndcg = ndcg_at_k(ids, grades, 3)
        assert abs(ndcg - 1.0) < 0.01

    def test_reverse_ranking(self):
        """When recommended order is reverse of ideal, NDCG should be < 1.0."""
        ids = [uuid.uuid4() for _ in range(3)]
        grades = {ids[0]: 1, ids[1]: 2, ids[2]: 3}
        ndcg = ndcg_at_k(ids, grades, 3)
        assert ndcg < 1.0
        assert ndcg > 0.0  # Should still be positive

    def test_empty_grades(self):
        assert ndcg_at_k([uuid.uuid4()], {}, 3) == 0.0

    def test_k_zero(self):
        assert ndcg_at_k([uuid.uuid4()], {uuid.uuid4(): 3}, 0) == 0.0

    def test_dcg_computation(self):
        """Verify DCG formula: sum of (2^grade - 1) / log2(rank + 1)."""
        ids = [uuid.uuid4() for _ in range(2)]
        grades = {ids[0]: 3, ids[1]: 1}
        dcg = dcg_at_k(ids, grades, 2)
        # Position 1: (2^3 - 1) / log2(2) = 7/1 = 7.0
        # Position 2: (2^1 - 1) / log2(3) = 1/1.585 = 0.631
        expected = 7.0 + 1.0 / 1.5849625
        assert abs(dcg - expected) < 0.01
