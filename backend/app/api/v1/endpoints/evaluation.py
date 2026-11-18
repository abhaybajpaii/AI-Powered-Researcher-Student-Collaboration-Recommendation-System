"""Evaluation / Benchmarking API endpoints.

Exposes the offline evaluation framework via REST, supporting:
- POST /evaluation/benchmark: Run comparative evaluation against relevance judgments
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db_session
from backend.app.api.v1.endpoints.admin import require_admin_privilege
from backend.app.evaluation.evaluator import benchmark_evaluator

router = APIRouter()


@router.post(
    "/benchmark",
    summary="Run Offline Benchmark Evaluation",
    description=(
        "Executes a comparative offline evaluation comparing the hybrid embedding "
        "recommender against the TF-IDF lexical baseline using stored relevance judgments. "
        "Computes Precision@K, Recall@K, NDCG@K, and MRR."
    ),
    dependencies=[Depends(require_admin_privilege)],
)
async def run_benchmark(
    benchmark_suite: str = Query(
        default="standard_eval_v1",
        description="Name of the benchmark suite to evaluate against",
    ),
    k_values: Optional[str] = Query(
        default="5,10",
        description="Comma-separated K values for Precision/Recall/NDCG (e.g., '5,10')",
    ),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Runs the full benchmark evaluation pipeline and returns comparative metrics."""
    parsed_k_values = [int(k.strip()) for k in (k_values or "5,10").split(",") if k.strip().isdigit()]
    if not parsed_k_values:
        parsed_k_values = [5, 10]

    result = await benchmark_evaluator.run_evaluation(
        db,
        benchmark_suite=benchmark_suite,
        k_values=parsed_k_values,
    )
    return result


class RelevanceJudgmentCreate(BaseModel):
    student_id: UUID
    faculty_id: UUID
    relevance_grade: int = Field(..., ge=0, le=3, description="0=Irrelevant, 1=Marginal, 2=Relevant, 3=Highly Relevant")
    benchmark_suite: str = Field(default="real_eval_v1")
    notes: Optional[str] = None
    annotator_id: Optional[str] = "admin_expert"


@router.post(
    "/judgments",
    summary="Create or Update Relevance Judgment",
    description="Records a verified human or expert relevance judgment for evaluating recommendations on real scholarly data.",
    dependencies=[Depends(require_admin_privilege)],
)
async def create_relevance_judgment(
    payload: RelevanceJudgmentCreate,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    from backend.app.models.evaluation import RelevanceJudgment
    from sqlalchemy import select

    stmt = select(RelevanceJudgment).where(
        RelevanceJudgment.student_id == payload.student_id,
        RelevanceJudgment.faculty_id == payload.faculty_id,
        RelevanceJudgment.benchmark_suite == payload.benchmark_suite,
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        existing.relevance_grade = payload.relevance_grade
        existing.notes = payload.notes
        existing.annotator_id = payload.annotator_id or existing.annotator_id
        await db.commit()
        await db.refresh(existing)
        return {
            "status": "updated",
            "judgment_id": str(existing.id),
            "relevance_grade": existing.relevance_grade,
            "benchmark_suite": existing.benchmark_suite,
        }

    judgment = RelevanceJudgment(
        student_id=payload.student_id,
        faculty_id=payload.faculty_id,
        relevance_grade=payload.relevance_grade,
        benchmark_suite=payload.benchmark_suite,
        annotator_id=payload.annotator_id or "admin_expert",
        notes=payload.notes,
    )
    db.add(judgment)
    await db.commit()
    await db.refresh(judgment)
    return {
        "status": "created",
        "judgment_id": str(judgment.id),
        "relevance_grade": judgment.relevance_grade,
        "benchmark_suite": judgment.benchmark_suite,
    }
