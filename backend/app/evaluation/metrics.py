import math
from typing import Dict, List, Set
from uuid import UUID


def precision_at_k(recommended_ids: List[UUID], relevant_ids: Set[UUID], k: int) -> float:
    """Calculates Precision@K: Fraction of top-K recommended items that are relevant."""
    if k <= 0 or not recommended_ids:
        return 0.0
    top_k_items = recommended_ids[:k]
    hits = sum(1 for item in top_k_items if item in relevant_ids)
    return round(float(hits / k), 4)


def recall_at_k(recommended_ids: List[UUID], relevant_ids: Set[UUID], k: int) -> float:
    """Calculates Recall@K: Fraction of all relevant items captured in top-K."""
    if not relevant_ids or k <= 0 or not recommended_ids:
        return 0.0
    top_k_items = recommended_ids[:k]
    hits = sum(1 for item in top_k_items if item in relevant_ids)
    return round(float(hits / len(relevant_ids)), 4)


def reciprocal_rank(recommended_ids: List[UUID], relevant_ids: Set[UUID]) -> float:
    """Calculates Reciprocal Rank (1/rank of first relevant recommendation)."""
    for rank, item in enumerate(recommended_ids, start=1):
        if item in relevant_ids:
            return round(float(1.0 / rank), 4)
    return 0.0


def dcg_at_k(recommended_ids: List[UUID], relevance_grades: Dict[UUID, int], k: int) -> float:
    """Computes Discounted Cumulative Gain at rank K using 2^grade - 1 formula."""
    dcg = 0.0
    for i, item_id in enumerate(recommended_ids[:k], start=1):
        grade = relevance_grades.get(item_id, 0)
        gain = (2.0 ** grade) - 1.0
        discount = math.log2(i + 1)
        dcg += gain / discount
    return dcg


def ndcg_at_k(recommended_ids: List[UUID], relevance_grades: Dict[UUID, int], k: int) -> float:
    """Calculates Normalized Discounted Cumulative Gain at rank K."""
    if not relevance_grades or k <= 0:
        return 0.0

    actual_dcg = dcg_at_k(recommended_ids, relevance_grades, k)

    # Calculate Ideal DCG (sort all known items descending by true relevance grade)
    ideal_sorted_ids = sorted(
        relevance_grades.keys(), key=lambda x: relevance_grades[x], reverse=True
    )
    ideal_dcg = dcg_at_k(ideal_sorted_ids, relevance_grades, k)

    if ideal_dcg <= 1e-12:
        return 0.0

    return round(float(actual_dcg / ideal_dcg), 4)
