from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.student import Student
from backend.app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    def __init__(self):
        super().__init__(Student)

    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Optional[Student]:
        stmt = select(Student).where(Student.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_with_details(self, db: AsyncSession, id: UUID) -> Optional[Student]:
        stmt = (
            select(Student)
            .where(Student.id == id)
            .options(
                selectinload(Student.skills_interests),
                selectinload(Student.academic_projects),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def filter_students(
        self,
        db: AsyncSession,
        *,
        department: Optional[str] = None,
        degree_level: Optional[str] = None,
        availability_status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Student]:
        stmt = select(Student)
        if department:
            stmt = stmt.where(Student.department == department)
        if degree_level:
            stmt = stmt.where(Student.degree_level == degree_level)
        if availability_status:
            stmt = stmt.where(Student.availability_status == availability_status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        db: AsyncSession,
        *,
        department: Optional[str] = None,
        degree_level: Optional[str] = None,
        availability_status: Optional[str] = None,
    ) -> int:
        stmt = select(func.count(Student.id))
        if department:
            stmt = stmt.where(Student.department == department)
        if degree_level:
            stmt = stmt.where(Student.degree_level == degree_level)
        if availability_status:
            stmt = stmt.where(Student.availability_status == availability_status)

        result = await db.execute(stmt)
        return result.scalar() or 0


student_repo = StudentRepository()
