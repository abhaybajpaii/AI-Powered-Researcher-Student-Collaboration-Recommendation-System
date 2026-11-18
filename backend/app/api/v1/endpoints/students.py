import uuid
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db_session
from backend.app.schemas.common import PaginatedResponse, PaginationParams
from backend.app.schemas.student import (
    AcademicProjectCreate,
    AcademicProjectResponse,
    StudentCreate,
    StudentDetailResponse,
    StudentResponse,
    StudentUpdate,
)
from backend.app.schemas.taxonomy import (
    StudentSkillInterestCreate,
    StudentSkillInterestResponse,
)
from backend.app.services.student_service import student_service

router = APIRouter()


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create student profile",
    description="Creates a new student profile linked to an existing user account.",
)
async def create_student(
    student_in: StudentCreate,
    db: AsyncSession = Depends(get_db_session),
):
    student = await student_service.create_student(db, student_in)
    return StudentResponse.model_validate(student)


@router.get(
    "",
    response_model=PaginatedResponse[StudentResponse],
    status_code=status.HTTP_200_OK,
    summary="List student profiles",
    description="Retrieves a paginated list of student profiles with multi-facet filtering.",
)
async def list_students(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    department: Optional[str] = Query(default=None, description="Filter by department"),
    degree_level: Optional[str] = Query(default=None, description="Filter by degree level"),
    availability_status: Optional[str] = Query(default=None, description="Filter by availability"),
    db: AsyncSession = Depends(get_db_session),
):
    params = PaginationParams(page=page, page_size=page_size)
    return await student_service.list_students(
        db,
        pagination=params,
        department=department,
        degree_level=degree_level,
        availability_status=availability_status,
    )


@router.get(
    "/{student_id}",
    response_model=StudentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student by ID",
    description="Retrieves a single student profile with skills, interests, and academic projects.",
)
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    student = await student_service.get_student_detail(db, student_id)
    return StudentDetailResponse.model_validate(student)


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update student profile",
    description="Updates fields of an existing student profile.",
)
async def update_student(
    student_id: UUID,
    student_in: StudentUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    student = await student_service.update_student(db, student_id, student_in)
    return StudentResponse.model_validate(student)


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete student profile",
    description="Deletes a student profile by ID.",
)
async def delete_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    await student_service.delete_student(db, student_id)
    return None


@router.post(
    "/{student_id}/projects",
    response_model=AcademicProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add academic project to student profile",
)
async def add_student_project(
    student_id: UUID,
    project_in: AcademicProjectCreate,
    db: AsyncSession = Depends(get_db_session),
):
    import uuid
    from backend.app.core.exceptions import EntityNotFoundException
    from backend.app.models.project import AcademicProject
    from backend.app.models.student import Student

    student = await db.get(Student, student_id)
    if not student:
        raise EntityNotFoundException("Student", student_id)

    project = AcademicProject(
        id=uuid.uuid4(),
        student_id=student_id,
        title=project_in.title,
        description=project_in.description,
        role=project_in.role,
        github_url=project_in.github_url,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return AcademicProjectResponse.model_validate(project)


@router.delete(
    "/{student_id}/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an academic project",
)
async def delete_student_project(
    student_id: UUID,
    project_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    from backend.app.core.exceptions import EntityNotFoundException
    from backend.app.models.project import AcademicProject

    project = await db.get(AcademicProject, project_id)
    if not project or project.student_id != student_id:
        raise EntityNotFoundException("AcademicProject", project_id)

    await db.delete(project)
    await db.commit()
    return None


@router.post(
    "/{student_id}/skills",
    response_model=StudentSkillInterestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add skill or interest to student profile",
)
async def add_student_skill(
    student_id: UUID,
    skill_in: StudentSkillInterestCreate,
    db: AsyncSession = Depends(get_db_session),
):
    import uuid
    from sqlalchemy.orm import selectinload
    from backend.app.core.exceptions import EntityConflictException, EntityNotFoundException
    from backend.app.models.student import Student
    from backend.app.models.taxonomy import StudentSkillInterest, TopicSkill

    student = await db.get(Student, student_id)
    if not student:
        raise EntityNotFoundException("Student", student_id)

    topic = await db.get(TopicSkill, skill_in.topic_skill_id)
    if not topic:
        raise EntityNotFoundException("TopicSkill", skill_in.topic_skill_id)

    stmt = select(StudentSkillInterest).where(
        StudentSkillInterest.student_id == student_id,
        StudentSkillInterest.topic_skill_id == skill_in.topic_skill_id,
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        existing.proficiency_level = skill_in.proficiency_level
        existing.interest_level = skill_in.interest_level
        existing.years_experience = skill_in.years_experience
        await db.commit()
        await db.refresh(existing)
        return StudentSkillInterestResponse.model_validate(existing)

    item = StudentSkillInterest(
        id=uuid.uuid4(),
        student_id=student_id,
        topic_skill_id=skill_in.topic_skill_id,
        proficiency_level=skill_in.proficiency_level,
        interest_level=skill_in.interest_level,
        years_experience=skill_in.years_experience,
    )
    db.add(item)
    await db.commit()

    refetched = (
        await db.execute(
            select(StudentSkillInterest)
            .where(StudentSkillInterest.id == item.id)
            .options(selectinload(StudentSkillInterest.topic_skill))
        )
    ).scalars().first()
    return StudentSkillInterestResponse.model_validate(refetched)


@router.delete(
    "/{student_id}/skills/{skill_interest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a skill or interest from student profile",
)
async def delete_student_skill(
    student_id: UUID,
    skill_interest_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    from backend.app.core.exceptions import EntityNotFoundException
    from backend.app.models.taxonomy import StudentSkillInterest

    item = await db.get(StudentSkillInterest, skill_interest_id)
    if not item or item.student_id != student_id:
        raise EntityNotFoundException("StudentSkillInterest", skill_interest_id)

    await db.delete(item)
    await db.commit()
    return None

