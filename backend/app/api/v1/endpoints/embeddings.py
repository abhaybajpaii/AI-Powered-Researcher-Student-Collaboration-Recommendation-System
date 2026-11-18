"""Embedding Management API endpoints.

Exposes the embedding pipeline via REST, supporting:
- POST /embeddings/sync: Synchronize all entity embeddings
- GET /embeddings/stats: View embedding statistics
- GET /embeddings/entity/{entity_type}/{entity_id}: Look up specific entity embedding
"""

from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db_session
from backend.app.api.v1.endpoints.admin import require_admin_privilege
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.embeddings.service import embedding_service
from backend.app.models.embedding import EmbeddingRecord

router = APIRouter()


@router.post(
    "/sync",
    summary="Synchronize All Embeddings",
    description="Generates or updates embeddings for all students, projects, faculty, and publications.",
    dependencies=[Depends(require_admin_privilege)],
)
async def sync_embeddings(
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Triggers full embedding synchronization across all entity types."""
    stats = await embedding_service.sync_all_embeddings(db)
    return {
        "status": "sync_complete",
        "model_name": embedding_service.model_name,
        "model_version": embedding_service.model_version,
        "dimension": embedding_service.dimension,
        **stats,
    }


@router.get(
    "/stats",
    summary="Embedding Statistics",
    description="Returns counts and breakdown of stored embeddings by entity type and model.",
    dependencies=[Depends(require_admin_privilege)],
)
async def get_embedding_stats(
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Provides aggregate statistics on stored embeddings."""
    # Total count
    total_stmt = select(func.count(EmbeddingRecord.id))
    total = (await db.execute(total_stmt)).scalar() or 0

    # Count by entity type
    type_stmt = (
        select(
            EmbeddingRecord.entity_type,
            func.count(EmbeddingRecord.id).label("count"),
        )
        .group_by(EmbeddingRecord.entity_type)
    )
    type_results = (await db.execute(type_stmt)).all()
    by_entity_type = {row[0]: row[1] for row in type_results}

    # Count by model name
    model_stmt = (
        select(
            EmbeddingRecord.model_name,
            EmbeddingRecord.model_version,
            func.count(EmbeddingRecord.id).label("count"),
        )
        .group_by(EmbeddingRecord.model_name, EmbeddingRecord.model_version)
    )
    model_results = (await db.execute(model_stmt)).all()
    by_model = [
        {"model_name": row[0], "model_version": row[1], "count": row[2]}
        for row in model_results
    ]

    return {
        "total_embeddings": total,
        "by_entity_type": by_entity_type,
        "by_model": by_model,
        "active_model": embedding_service.model_name,
        "active_dimension": embedding_service.dimension,
    }


@router.get(
    "/entity/{entity_type}/{entity_id}",
    summary="Get Entity Embedding",
    description="Retrieves the stored embedding for a specific entity.",
    dependencies=[Depends(require_admin_privilege)],
)
async def get_entity_embedding(
    entity_type: str,
    entity_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Returns the embedding record for the specified entity."""
    stmt = select(EmbeddingRecord).where(
        EmbeddingRecord.entity_type == entity_type.upper(),
        EmbeddingRecord.entity_id == entity_id,
    )
    records = list((await db.execute(stmt)).scalars().all())

    if not records:
        raise EntityNotFoundException("Embedding", f"{entity_type}/{entity_id}")

    return {
        "entity_type": entity_type.upper(),
        "entity_id": str(entity_id),
        "embeddings": [
            {
                "id": str(rec.id),
                "embedding_type": rec.embedding_type,
                "model_name": rec.model_name,
                "model_version": rec.model_version,
                "dimension": len(rec.vector) if rec.vector else 0,
                "created_at": rec.created_at.isoformat() if hasattr(rec, "created_at") else None,
            }
            for rec in records
        ],
    }
