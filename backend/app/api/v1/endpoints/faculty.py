from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db_session
from backend.app.schemas.common import PaginatedResponse, PaginationParams
from backend.app.schemas.faculty import (
    FacultyCreate,
    FacultyDetailResponse,
    FacultyResponse,
    FacultyUpdate,
)
from backend.app.services.faculty_service import faculty_service

router = APIRouter()


@router.post(
    "",
    response_model=FacultyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create faculty profile",
    description="Creates a new faculty profile linked to an existing user account.",
)
async def create_faculty(
    faculty_in: FacultyCreate,
    db: AsyncSession = Depends(get_db_session),
):
    faculty = await faculty_service.create_faculty(db, faculty_in)
    return FacultyResponse.model_validate(faculty)


@router.get(
    "",
    response_model=PaginatedResponse[FacultyResponse],
    status_code=status.HTTP_200_OK,
    summary="List faculty profiles",
    description="Retrieves a paginated list of faculty profiles with department, availability, and search filtering.",
)
async def list_faculty(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    department: Optional[str] = Query(default=None, description="Filter by department"),
    accepting_students: Optional[bool] = Query(default=None, description="Filter by availability status"),
    min_capacity: Optional[int] = Query(default=None, ge=1, description="Filter by minimum open capacity"),
    search: Optional[str] = Query(default=None, description="Search by faculty name, department, lab, bio, or research expertise"),
    db: AsyncSession = Depends(get_db_session),
):
    params = PaginationParams(page=page, page_size=page_size)
    return await faculty_service.list_faculty(
        db,
        pagination=params,
        department=department,
        accepting_students=accepting_students,
        min_capacity=min_capacity,
        search=search,
    )


@router.get(
    "/{faculty_id}",
    response_model=FacultyDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get faculty by ID",
    description="Retrieves a single faculty profile with expertise and publication authorship.",
)
async def get_faculty(
    faculty_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    faculty = await faculty_service.get_faculty_detail(db, faculty_id)
    return FacultyDetailResponse.model_validate(faculty)


@router.put(
    "/{faculty_id}",
    response_model=FacultyResponse,
    status_code=status.HTTP_200_OK,
    summary="Update faculty profile",
    description="Updates fields of an existing faculty profile.",
)
async def update_faculty(
    faculty_id: UUID,
    faculty_in: FacultyUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    faculty = await faculty_service.update_faculty(db, faculty_id, faculty_in)
    return FacultyResponse.model_validate(faculty)


@router.delete(
    "/{faculty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete faculty profile",
    description="Deletes a faculty profile by ID.",
)
async def delete_faculty(
    faculty_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    await faculty_service.delete_faculty(db, faculty_id)
    return None
