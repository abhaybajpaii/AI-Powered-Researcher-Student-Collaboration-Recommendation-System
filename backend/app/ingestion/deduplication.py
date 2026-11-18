from typing import Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.publication import Publication
from backend.app.models.taxonomy import TopicSkill
from backend.app.models.user import User


async def find_existing_publication(
    db: AsyncSession,
    *,
    doi: Optional[str] = None,
    title_hash: Optional[str] = None,
) -> Optional[Publication]:
    """Finds an existing publication using normalized DOI or deterministic title hash."""
    conditions = []
    if doi:
        conditions.append(Publication.doi == doi)
    if title_hash:
        conditions.append(Publication.title_hash == title_hash)

    if not conditions:
        return None

    stmt = select(Publication).where(or_(*conditions))
    result = await db.execute(stmt)
    return result.scalars().first()


async def find_existing_topic(
    db: AsyncSession,
    *,
    slug: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[TopicSkill]:
    """Finds an existing topic/skill by slug or canonical name."""
    conditions = []
    if slug:
        conditions.append(TopicSkill.slug == slug)
    if name:
        conditions.append(TopicSkill.name == name)

    if not conditions:
        return None

    stmt = select(TopicSkill).where(or_(*conditions))
    result = await db.execute(stmt)
    return result.scalars().first()


async def find_existing_user(
    db: AsyncSession,
    email: str,
) -> Optional[User]:
    """Finds an existing user by email address."""
    stmt = select(User).where(User.email == email.strip().lower())
    result = await db.execute(stmt)
    return result.scalars().first()
