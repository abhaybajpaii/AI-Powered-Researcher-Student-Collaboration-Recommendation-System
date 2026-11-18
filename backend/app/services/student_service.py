from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import EntityConflictException, EntityNotFoundException
from backend.app.models.student import Student
from backend.app.models.user import User
from backend.app.repositories.student_repo import student_repo
from backend.app.schemas.common import PaginatedResponse, PaginationParams
from backend.app.schemas.student import StudentCreate, StudentResponse, StudentUpdate


class StudentService:
    async def get_student(self, db: AsyncSession, student_id: UUID) -> Student:
        student = await student_repo.get(db, student_id)
        if not student:
            raise EntityNotFoundException("Student", student_id)
        return student

    async def get_student_detail(self, db: AsyncSession, student_id: UUID) -> Student:
        student = await student_repo.get_with_details(db, student_id)
        if not student:
            raise EntityNotFoundException("Student", student_id)
        return student

    async def list_students(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        department: Optional[str] = None,
        degree_level: Optional[str] = None,
        availability_status: Optional[str] = None,
    ) -> PaginatedResponse[StudentResponse]:
        items = await student_repo.filter_students(
            db,
            department=department,
            degree_level=degree_level,
            availability_status=availability_status,
            offset=pagination.offset,
            limit=pagination.page_size,
        )
        total = await student_repo.count_filtered(
            db,
            department=department,
            degree_level=degree_level,
            availability_status=availability_status,
        )
        return PaginatedResponse.create(
            items=[StudentResponse.model_validate(item) for item in items],
            total=total,
            params=pagination,
        )

    async def create_student(
        self, db: AsyncSession, student_in: StudentCreate
    ) -> Student:
        # Check user exists
        user = await db.get(User, student_in.user_id)
        if not user:
            raise EntityNotFoundException("User", student_in.user_id)

        # Check existing student profile
        existing = await student_repo.get_by_user_id(db, student_in.user_id)
        if existing:
            raise EntityConflictException(
                f"A student profile already exists for user ID '{student_in.user_id}'.",
                code="STUDENT_PROFILE_EXISTS",
            )

        return await student_repo.create(db, obj_in=student_in.model_dump())

    async def update_student(
        self, db: AsyncSession, student_id: UUID, student_in: StudentUpdate
    ) -> Student:
        student = await self.get_student(db, student_id)
        return await student_repo.update(db, db_obj=student, obj_in=student_in)

    async def delete_student(self, db: AsyncSession, student_id: UUID) -> None:
        student = await self.get_student(db, student_id)
        await student_repo.delete(db, id=student.id)


student_service = StudentService()
