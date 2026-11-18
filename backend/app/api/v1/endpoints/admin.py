from typing import Any, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user, get_db_session
from backend.app.models.user import User
from backend.app.schemas.common import PaginatedResponse, PaginationParams
from backend.app.services.admin_service import admin_service
from backend.app.synthetic.generator import SyntheticConfig

router = APIRouter()


async def require_admin_privilege(
    auth: User = Depends(get_current_user),
) -> User:
    """Require an authenticated, active administrator account."""
    if auth.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Administrative privileges required. User has role '{auth.role}'.",
        )

    return auth


class SeedRequest(BaseModel):
    config: Optional[SyntheticConfig] = Field(default=None, description="Synthetic data generator configuration parameters")
    reset_existing: bool = Field(default=False, description="If true, safely purges existing synthetic records prior to seeding")


@router.post(
    "/seed-synthetic",
    status_code=status.HTTP_200_OK,
    summary="Generate & Seed Synthetic Dataset",
    description="Generates synthetic academic entities (students, faculty, publications, skills, judgments) and ingests them into the database.",
    dependencies=[Depends(require_admin_privilege)],
)
async def seed_synthetic(
    request: SeedRequest = SeedRequest(),
    db: AsyncSession = Depends(get_db_session),
):
    return await admin_service.seed_synthetic_dataset(
        db, config=request.config, reset_existing=request.reset_existing
    )


@router.post(
    "/reset-synthetic",
    status_code=status.HTTP_200_OK,
    summary="Purge Synthetic Dataset",
    description="Safely removes all records originating from SYNTHETIC data sources. Real research records are never affected.",
    dependencies=[Depends(require_admin_privilege)],
)
async def reset_synthetic(
    db: AsyncSession = Depends(get_db_session),
):
    return await admin_service.reset_synthetic_data(db)


@router.get(
    "/import-jobs",
    response_model=PaginatedResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List Data Import Jobs",
    description="Retrieves a paginated list of all data import jobs with status and record counts.",
    dependencies=[Depends(require_admin_privilege)],
)
async def list_import_jobs(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db_session),
):
    params = PaginationParams(page=page, page_size=page_size)
    return await admin_service.list_import_jobs(db, pagination=params)


@router.get(
    "/import-jobs/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Import Job Details",
    description="Retrieves detailed status, records processed, and error logs for an import job.",
    dependencies=[Depends(require_admin_privilege)],
)
async def get_import_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    return await admin_service.get_import_job(db, job_id)


@router.get(
    "/data-counts",
    status_code=status.HTTP_200_OK,
    summary="View Data Counts by Entity and Mode",
    description="Returns aggregate entity counts broken down by data mode (synthetic vs real/other).",
    dependencies=[Depends(require_admin_privilege)],
)
async def get_data_counts(
    db: AsyncSession = Depends(get_db_session),
):
    return await admin_service.get_data_counts(db)


@router.post(
    "/validate-records",
    status_code=status.HTTP_200_OK,
    summary="Validate Inbound Data Batch",
    description="Validates a batch payload against ingestion schemas without inserting records into the database.",
    dependencies=[Depends(require_admin_privilege)],
)
async def validate_records(
    payload: Dict[str, Any],
):
    return admin_service.validate_batch(payload)
