from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db_session
from backend.app.models.taxonomy import TopicSkill
from backend.app.schemas.taxonomy import TopicSkillResponse

router = APIRouter()


@router.get(
    "/topics",
    response_model=List[TopicSkillResponse],
    summary="List taxonomy topics and skills",
    description="Retrieves taxonomy skills and research topics for search, filters, and profile selection.",
)
async def list_topics(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    search: Optional[str] = Query(default=None, description="Search by name"),
    db: AsyncSession = Depends(get_db_session),
) -> List[TopicSkillResponse]:
    stmt = select(TopicSkill).order_by(TopicSkill.category, TopicSkill.name)
    if category:
        stmt = stmt.where(TopicSkill.category == category.upper())
    if search:
        stmt = stmt.where(TopicSkill.name.ilike(f"%{search.strip()}%"))

    result = await db.execute(stmt)
    records = result.scalars().all()
    return [TopicSkillResponse.model_validate(r) for r in records]
