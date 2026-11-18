"""Scholarly Research Data & Verification API Endpoints.

Provides administrative controls for:
- OpenAlex scholarly search (works, authors, institutions)
- Crossref publication lookup & conflict resolution
- Selective record imports with deduplication and vector embedding
- Institutional CSV faculty roster upload
- Faculty verification review & status tracking
- Import job inspection
"""

import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db_session
from backend.app.api.v1.endpoints.admin import require_admin_privilege
from backend.app.connectors.crossref_client import crossref_client
from backend.app.connectors.openalex_client import openalex_client
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.ingestion.real_data_service import real_research_data_service
from backend.app.models.faculty import Faculty
from backend.app.models.provenance import ImportJob

router = APIRouter()


# -----------------------------------------------------------------------------
# 1. OpenAlex & Crossref Search / Preview Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/search/works",
    summary="Search OpenAlex Scholarly Works",
    description="Searches genuine publications via OpenAlex with optional institution ROR and year filtering.",
    dependencies=[Depends(require_admin_privilege)],
)
async def search_openalex_works(
    query: str = Query(..., min_length=2, description="Search terms, paper title, or topic"),
    institution_ror: Optional[str] = Query(None, description="Optional ROR identifier for institution filter"),
    year: Optional[int] = Query(None, description="Filter from publication year onward"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    return await openalex_client.search_works(
        query=query,
        institution_ror=institution_ror,
        page=page,
        per_page=per_page,
        from_publication_year=year,
    )


@router.get(
    "/search/authors",
    summary="Search OpenAlex Researchers / Authors",
    description="Searches genuine scholar profiles via OpenAlex with optional institution filter.",
    dependencies=[Depends(require_admin_privilege)],
)
async def search_openalex_authors(
    query: str = Query(..., min_length=2, description="Author / researcher name or query"),
    institution_ror: Optional[str] = Query(None, description="Optional ROR identifier for institution filter"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    return await openalex_client.search_authors(
        query=query,
        institution_ror=institution_ror,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/search/institutions",
    summary="Search Academic Institutions",
    description="Looks up university ROR and OpenAlex identifiers.",
    dependencies=[Depends(require_admin_privilege)],
)
async def search_institutions(
    query: str = Query(..., min_length=2, description="University or research institution name"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5, ge=1, le=20),
) -> List[Dict[str, Any]]:
    return await openalex_client.search_institutions(query=query, page=page, per_page=per_page)


@router.get(
    "/crossref/{doi:path}",
    summary="Lookup Publication via Crossref DOI",
    description="Retrieves metadata from Crossref to enrich or verify a publication.",
    dependencies=[Depends(require_admin_privilege)],
)
async def lookup_crossref(doi: str) -> Dict[str, Any]:
    res = await crossref_client.get_work_by_doi(doi)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publication with DOI '{doi}' was not found on Crossref.",
        )
    return res


# -----------------------------------------------------------------------------
# 2. Ingestion & Import Execution Endpoints
# -----------------------------------------------------------------------------

class ImportWorksRequest(BaseModel):
    works: List[Dict[str, Any]] = Field(..., min_length=1)
    enrich_crossref: bool = True
    auto_embed: bool = True


@router.post(
    "/import/works",
    summary="Import Selected OpenAlex Works",
    description="Persists selected OpenAlex publications into PostgreSQL with Crossref enrichment, deduplication, and vector embeddings.",
    dependencies=[Depends(require_admin_privilege)],
)
async def import_works(
    payload: ImportWorksRequest,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    return await real_research_data_service.import_openalex_works(
        db,
        works_data=payload.works,
        enrich_with_crossref=payload.enrich_crossref,
        auto_embed=payload.auto_embed,
    )


class ImportAuthorsRequest(BaseModel):
    authors: List[Dict[str, Any]] = Field(..., min_length=1)
    default_department: str = Field(default="Computer Science")
    default_status: str = Field(
        default="PENDING_REVIEW",
        description="Initial verification status: PENDING_REVIEW or UNVERIFIED",
    )
    auto_embed: bool = True


@router.post(
    "/import/authors",
    summary="Import Selected OpenAlex Researchers",
    description="Imports scholarly authors into the faculty database with UNVERIFIED or PENDING_REVIEW status for administrator verification.",
    dependencies=[Depends(require_admin_privilege)],
)
async def import_authors(
    payload: ImportAuthorsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    return await real_research_data_service.import_openalex_authors(
        db,
        authors_data=payload.authors,
        default_department=payload.default_department,
        default_status=payload.default_status,
        auto_embed=payload.auto_embed,
    )


class CsvImportRequest(BaseModel):
    csv_text: str = Field(..., min_length=10)
    auto_embed: bool = True


@router.post(
    "/import/csv",
    summary="Import Verified Faculty from Institutional CSV",
    description="Ingests official university faculty roster with VERIFIED status.",
    dependencies=[Depends(require_admin_privilege)],
)
async def import_csv_roster(
    payload: CsvImportRequest,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    return await real_research_data_service.import_institutional_csv_roster(
        db,
        csv_text=payload.csv_text,
        auto_embed=payload.auto_embed,
    )


# -----------------------------------------------------------------------------
# 3. Overview Summary & Import Jobs Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/summary",
    summary="Real vs. Synthetic Data Summary",
    description="Returns aggregate counts of real vs synthetic faculty, publications, and verification statuses.",
    dependencies=[Depends(require_admin_privilege)],
)
async def get_data_summary(
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    return await real_research_data_service.get_data_summary(db)


@router.get(
    "/jobs",
    summary="List Ingestion & Import Jobs",
    description="Returns audit trail of past import jobs, status, and error logs.",
    dependencies=[Depends(require_admin_privilege)],
)
async def list_import_jobs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    stmt = select(ImportJob).order_by(desc(ImportJob.started_at)).limit(limit)
    jobs = list((await db.execute(stmt)).scalars().all())
    return [
        {
            "id": str(j.id),
            "data_source_id": str(j.data_source_id),
            "status": j.status,
            "records_processed": j.records_processed,
            "records_created": j.records_created,
            "records_updated": j.records_updated,
            "error_log": j.error_log,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        }
        for j in jobs
    ]


@router.post(
    "/jobs/{job_id}/retry",
    summary="Retry a Failed Import Job",
    description="Retry is not currently implemented; this endpoint does not change job state.",
    dependencies=[Depends(require_admin_privilege)],
)
async def retry_import_job(
    job_id: UUID,
) -> Dict[str, Any]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Import job retries are not implemented; no job state was changed.",
    )


# -----------------------------------------------------------------------------
# 4. Faculty Verification Workflow Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/verification/faculty",
    summary="List Faculty for Verification Review",
    description="Lists faculty members filterable by verification status, synthetic flag, and department.",
    dependencies=[Depends(require_admin_privilege)],
)
async def list_faculty_verification(
    status_filter: Optional[str] = Query(None, description="UNVERIFIED, PENDING_REVIEW, VERIFIED, REJECTED_OUTDATED"),
    is_synthetic: Optional[bool] = Query(None),
    department: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    stmt = select(Faculty)
    if status_filter:
        stmt = stmt.where(Faculty.verification_status == status_filter)
    if is_synthetic is not None:
        stmt = stmt.where(Faculty.is_synthetic == is_synthetic)
    if department:
        stmt = stmt.where(Faculty.department == department)

    count_stmt = select(func.count(Faculty.id))
    if status_filter:
        count_stmt = count_stmt.where(Faculty.verification_status == status_filter)
    if is_synthetic is not None:
        count_stmt = count_stmt.where(Faculty.is_synthetic == is_synthetic)
    if department:
        count_stmt = count_stmt.where(Faculty.department == department)

    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(Faculty.last_name, Faculty.first_name).offset((page - 1) * per_page).limit(per_page)
    items = list((await db.execute(stmt)).scalars().all())

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": str(f.id),
                "first_name": f.first_name,
                "last_name": f.last_name,
                "department": f.department,
                "title_rank": f.title_rank,
                "lab_name": f.lab_name,
                "accepting_students": f.accepting_students,
                "is_synthetic": f.is_synthetic,
                "verification_status": f.verification_status,
                "openalex_id": f.openalex_id,
                "institution_name": f.institution_name,
                "verification_notes": f.verification_notes,
                "verified_at": f.verified_at.isoformat() if f.verified_at else None,
            }
            for f in items
        ],
    }


class UpdateFacultyVerificationRequest(BaseModel):
    verification_status: str = Field(..., description="UNVERIFIED, PENDING_REVIEW, VERIFIED, REJECTED_OUTDATED")
    verification_notes: Optional[str] = None
    department: Optional[str] = None
    title_rank: Optional[str] = None
    accepting_students: Optional[bool] = None


@router.put(
    "/verification/faculty/{faculty_id}",
    summary="Update Faculty Verification Status",
    description="Updates verification status, notes, and academic role for a faculty member.",
    dependencies=[Depends(require_admin_privilege)],
)
async def update_faculty_verification(
    faculty_id: UUID,
    payload: UpdateFacultyVerificationRequest,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    fac = await db.get(Faculty, faculty_id)
    if not fac:
        raise EntityNotFoundException("Faculty", faculty_id)

    fac.verification_status = payload.verification_status
    if payload.verification_notes is not None:
        fac.verification_notes = payload.verification_notes
    if payload.department:
        fac.department = payload.department
    if payload.title_rank:
        fac.title_rank = payload.title_rank
    if payload.accepting_students is not None:
        fac.accepting_students = payload.accepting_students

    if payload.verification_status == "VERIFIED":
        fac.verified_at = datetime.datetime.now(datetime.timezone.utc)
    elif payload.verification_status in ("UNVERIFIED", "REJECTED_OUTDATED"):
        fac.verified_at = None

    await db.commit()
    await db.refresh(fac)

    return {
        "status": "updated",
        "faculty_id": str(fac.id),
        "verification_status": fac.verification_status,
        "verified_at": fac.verified_at.isoformat() if fac.verified_at else None,
    }


class BatchVerificationRequest(BaseModel):
    faculty_ids: List[UUID] = Field(..., min_length=1)
    action: str = Field(..., description="'VERIFY' or 'REJECT'")
    notes: Optional[str] = None


@router.post(
    "/verification/faculty/batch",
    summary="Batch Faculty Verification",
    description="Verifies or rejects multiple faculty profiles in a single administrative transaction.",
    dependencies=[Depends(require_admin_privilege)],
)
async def batch_faculty_verification(
    payload: BatchVerificationRequest,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    new_status = "VERIFIED" if payload.action.upper() == "VERIFY" else "REJECTED_OUTDATED"
    stmt = select(Faculty).where(Faculty.id.in_(payload.faculty_ids))
    faculty_list = list((await db.execute(stmt)).scalars().all())

    updated_count = 0
    now = datetime.datetime.now(datetime.timezone.utc)

    for fac in faculty_list:
        fac.verification_status = new_status
        if payload.notes:
            fac.verification_notes = payload.notes
        if new_status == "VERIFIED":
            fac.verified_at = now
        else:
            fac.verified_at = None
        updated_count += 1

    await db.commit()

    return {
        "action": payload.action,
        "updated_count": updated_count,
        "new_status": new_status,
    }
