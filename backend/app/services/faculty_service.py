from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import EntityConflictException, EntityNotFoundException
from backend.app.models.faculty import Faculty
from backend.app.models.user import User
from backend.app.repositories.faculty_repo import faculty_repo
from backend.app.schemas.common import PaginatedResponse, PaginationParams
from backend.app.schemas.faculty import FacultyCreate, FacultyResponse, FacultyUpdate


class FacultyService:
    async def get_faculty(self, db: AsyncSession, faculty_id: UUID) -> Faculty:
        faculty = await faculty_repo.get(db, faculty_id)
        if not faculty:
            raise EntityNotFoundException("Faculty", faculty_id)
        return faculty

    async def get_faculty_detail(self, db: AsyncSession, faculty_id: UUID) -> Faculty:
        faculty = await faculty_repo.get_with_details(db, faculty_id)
        if not faculty:
            raise EntityNotFoundException("Faculty", faculty_id)
        return faculty

    async def list_faculty(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        department: Optional[str] = None,
        accepting_students: Optional[bool] = None,
        min_capacity: Optional[int] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[FacultyResponse]:
        items = await faculty_repo.filter_faculty(
            db,
            department=department,
            accepting_students=accepting_students,
            min_capacity=min_capacity,
            search=search,
            offset=pagination.offset,
            limit=pagination.page_size,
        )
        total = await faculty_repo.count_filtered(
            db,
            department=department,
            accepting_students=accepting_students,
            min_capacity=min_capacity,
            search=search,
        )
        return PaginatedResponse.create(
            items=[FacultyResponse.model_validate(item) for item in items],
            total=total,
            params=pagination,
        )

    async def create_faculty(
        self, db: AsyncSession, faculty_in: FacultyCreate
    ) -> Faculty:
        # Check user exists
        user = await db.get(User, faculty_in.user_id)
        if not user:
            raise EntityNotFoundException("User", faculty_in.user_id)

        # Check existing faculty profile
        existing = await faculty_repo.get_by_user_id(db, faculty_in.user_id)
        if existing:
            raise EntityConflictException(
                f"A faculty profile already exists for user ID '{faculty_in.user_id}'.",
                code="FACULTY_PROFILE_EXISTS",
            )

        return await faculty_repo.create(db, obj_in=faculty_in.model_dump())

    async def update_faculty(
        self, db: AsyncSession, faculty_id: UUID, faculty_in: FacultyUpdate
    ) -> Faculty:
        faculty = await self.get_faculty(db, faculty_id)
        return await faculty_repo.update(db, db_obj=faculty, obj_in=faculty_in)

    async def delete_faculty(self, db: AsyncSession, faculty_id: UUID) -> None:
        faculty = await self.get_faculty(db, faculty_id)
        await faculty_repo.delete(db, id=faculty.id)


faculty_service = FacultyService()
