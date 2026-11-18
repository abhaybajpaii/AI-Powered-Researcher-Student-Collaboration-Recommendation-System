"""Recommendation API endpoints.

Exposes the hybrid recommendation engine via REST, supporting:
- POST /recommendations/generate: Generate ranked faculty recommendations for a student
- GET /recommendations/runs/{run_id}: Retrieve a past recommendation run with results
- GET /recommendations/history/{student_id}: List recommendation history for a student
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.api.deps import get_db_session
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.models.recommendation import RecommendationResult, RecommendationRun
from backend.app.recommendations.engine import recommendation_engine
from backend.app.recommendations.schemas import (
    RecommendationRequest,
    RecommendationResponse,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=RecommendationResponse,
    summary="Generate Faculty Recommendations",
    description="Generates ranked faculty recommendations for a given student using the hybrid multi-signal recommendation engine.",
)
async def generate_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db_session),
) -> RecommendationResponse:
    """Triggers the full recommendation pipeline:
    1. Retrieves/generates student and faculty embeddings
    2. Computes multi-signal scores (research interest, project, publication, skill)
    3. Applies dynamic weight normalization
    4. Returns ranked results with evidence-based explanations
    """
    return await recommendation_engine.generate_recommendations(db, request)


@router.get(
    "/runs/{run_id}",
    summary="Get Recommendation Run Details",
    description="Retrieves a past recommendation run with all scored results.",
)
async def get_recommendation_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Returns full details of a prior recommendation run including all results."""
    stmt = (
        select(RecommendationRun)
        .where(RecommendationRun.id == run_id)
        .options(selectinload(RecommendationRun.results))
    )
    run = (await db.execute(stmt)).scalars().first()
    if not run:
        raise EntityNotFoundException("RecommendationRun", run_id)

    return {
        "run_id": run.id,
        "student_id": run.student_id,
        "algorithm_version": run.algorithm_version,
        "parameters": run.parameters,
        "execution_time_ms": run.execution_time_ms,
        "created_at": run.created_at.isoformat(),
        "results": [
            {
                "faculty_id": r.faculty_id,
                "rank_position": r.rank_position,
                "overall_score": r.overall_score,
                "semantic_score": r.semantic_score,
                "skill_score": r.skill_score,
                "project_score": r.project_score,
                "explanation_data": r.explanation_data,
                "user_interacted": r.user_interacted,
                "feedback_rating": r.feedback_rating,
                "feedback_notes": r.feedback_notes,
            }
            for r in sorted(run.results, key=lambda x: x.rank_position)
        ],
    }


@router.get(
    "/history/{student_id}",
    summary="Get Student Recommendation History",
    description="Lists all past recommendation runs for a given student.",
)
async def get_recommendation_history(
    student_id: UUID,
    limit: int = Query(default=20, ge=1, le=100, description="Max runs to return"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Returns a list of past recommendation runs for the specified student."""
    stmt = (
        select(RecommendationRun)
        .where(RecommendationRun.student_id == student_id)
        .order_by(RecommendationRun.created_at.desc())
        .limit(limit)
    )
    runs = list((await db.execute(stmt)).scalars().all())

    return {
        "student_id": student_id,
        "total_runs": len(runs),
        "runs": [
            {
                "run_id": r.id,
                "algorithm_version": r.algorithm_version,
                "execution_time_ms": r.execution_time_ms,
                "created_at": r.created_at.isoformat(),
            }
            for r in runs
        ],
    }


@router.post(
    "/runs/{run_id}/results/{faculty_id}/feedback",
    summary="Submit Recommendation Feedback",
    description="Records user feedback on a specific recommendation result.",
)
async def submit_feedback(
    run_id: UUID,
    faculty_id: UUID,
    rating: int = Query(ge=1, le=5, description="User rating 1-5"),
    notes: Optional[str] = Query(default=None, max_length=1000),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Records user interaction and feedback on a recommendation result."""
    stmt = select(RecommendationResult).where(
        RecommendationResult.run_id == run_id,
        RecommendationResult.faculty_id == faculty_id,
    )
    result = (await db.execute(stmt)).scalars().first()
    if not result:
        raise EntityNotFoundException("RecommendationResult", f"{run_id}/{faculty_id}")

    result.user_interacted = True
    result.feedback_rating = rating
    result.feedback_notes = notes
    db.add(result)
    await db.commit()

    return {
        "status": "feedback_recorded",
        "run_id": run_id,
        "faculty_id": faculty_id,
        "rating": rating,
    }
