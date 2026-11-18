from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.faculty import Faculty
from backend.app.models.publication import PublicationAuthorship
from backend.app.models.taxonomy import FacultySkillExpertise, TopicSkill
from backend.app.repositories.base import BaseRepository


class FacultyRepository(BaseRepository[Faculty]):
    def __init__(self):
        super().__init__(Faculty)

    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Optional[Faculty]:
        stmt = select(Faculty).where(Faculty.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_with_details(self, db: AsyncSession, id: UUID) -> Optional[Faculty]:
        stmt = (
            select(Faculty)
            .where(Faculty.id == id)
            .options(
                selectinload(Faculty.skills_expertise),
                selectinload(Faculty.authorship_links).selectinload(PublicationAuthorship.publication),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    def _apply_filters(
        self,
        stmt,
        *,
        department: Optional[str] = None,
        accepting_students: Optional[bool] = None,
        min_capacity: Optional[int] = None,
        search: Optional[str] = None,
    ):
        if department:
            stmt = stmt.where(Faculty.department == department)
        if accepting_students is not None:
            stmt = stmt.where(Faculty.accepting_students == accepting_students)
        if min_capacity is not None:
            stmt = stmt.where((Faculty.max_capacity - Faculty.current_student_count) >= min_capacity)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Faculty.first_name.ilike(pattern),
                    Faculty.last_name.ilike(pattern),
                    (Faculty.first_name + " " + Faculty.last_name).ilike(pattern),
                    Faculty.department.ilike(pattern),
                    Faculty.lab_name.ilike(pattern),
                    Faculty.bio.ilike(pattern),
                    Faculty.skills_expertise.any(
                        FacultySkillExpertise.topic_skill.has(TopicSkill.name.ilike(pattern))
                    ),
                )
            )
        return stmt

    async def filter_faculty(
        self,
        db: AsyncSession,
        *,
        department: Optional[str] = None,
        accepting_students: Optional[bool] = None,
        min_capacity: Optional[int] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Faculty]:
        stmt = select(Faculty)
        stmt = self._apply_filters(
            stmt,
            department=department,
            accepting_students=accepting_students,
            min_capacity=min_capacity,
            search=search,
        )
        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        db: AsyncSession,
        *,
        department: Optional[str] = None,
        accepting_students: Optional[bool] = None,
        min_capacity: Optional[int] = None,
        search: Optional[str] = None,
    ) -> int:
        stmt = select(func.count(Faculty.id))
        stmt = self._apply_filters(
            stmt,
            department=department,
            accepting_students=accepting_students,
            min_capacity=min_capacity,
            search=search,
        )
        result = await db.execute(stmt)
        return result.scalar() or 0


faculty_repo = FacultyRepository()
