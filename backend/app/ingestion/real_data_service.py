"""Real Research Data Ingestion Service.

Orchestrates scholarly metadata ingestion from OpenAlex and Crossref, institutional CSV roster imports,
non-destructive deduplication, provenance logging, verification tracking, and automatic vector embedding.
"""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.connectors.crossref_client import crossref_client
from backend.app.connectors.csv_importer import csv_importer
from backend.app.connectors.openalex_client import openalex_client
from backend.app.core.security import get_password_hash
from backend.app.embeddings.service import embedding_service
from backend.app.ingestion.deduplication import find_existing_publication
from backend.app.ingestion.preprocessing import generate_title_hash, normalize_doi, normalize_text
from backend.app.models.faculty import Faculty
from backend.app.models.provenance import DataSource, EntityProvenance, ImportJob
from backend.app.models.publication import Publication, PublicationAuthorship
from backend.app.models.user import User

logger = logging.getLogger(__name__)


class RealResearchDataService:
    """Manages genuine scholarly data ingestion from OpenAlex, Crossref, and institutional rosters."""

    async def _get_or_create_data_source(
        self,
        db: AsyncSession,
        name: str,
        source_type: str,
        base_url: Optional[str] = None,
    ) -> DataSource:
        stmt = select(DataSource).where(DataSource.name == name)
        ds = (await db.execute(stmt)).scalars().first()
        if not ds:
            ds = DataSource(
                id=uuid.uuid4(),
                name=name,
                source_type=source_type,
                base_url=base_url,
                is_active=True,
            )
            db.add(ds)
            await db.flush()
        return ds

    async def import_openalex_works(
        self,
        db: AsyncSession,
        works_data: List[Dict[str, Any]],
        enrich_with_crossref: bool = True,
        auto_embed: bool = True,
    ) -> Dict[str, Any]:
        """Imports selected OpenAlex works records into the database with deduplication & provenance."""
        ds = await self._get_or_create_data_source(
            db, "OpenAlex Works", "OPENALEX", "https://api.openalex.org/works"
        )

        job = ImportJob(
            id=uuid.uuid4(),
            data_source_id=ds.id,
            status="RUNNING",
            started_at=datetime.datetime.now(datetime.timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            error_log=[],
        )
        db.add(job)
        await db.flush()

        created_pubs = []
        errors = []

        for work in works_data:
            job.records_processed += 1
            try:
                title = normalize_text(work.get("title") or "")
                abstract = normalize_text(work.get("abstract") or "")
                doi = normalize_doi(work.get("doi"))
                venue = work.get("venue")
                year = work.get("publication_year")
                citations = work.get("citation_count", 0)
                openalex_id = work.get("openalex_id") or work.get("id")

                # Optional Crossref enrichment
                if enrich_with_crossref and doi:
                    try:
                        crossref_data = await crossref_client.get_work_by_doi(doi)
                        if crossref_data:
                            work = crossref_client.resolve_conflicts(work, crossref_data)
                            abstract = normalize_text(work.get("abstract") or abstract)
                            venue = work.get("venue") or venue
                            year = work.get("publication_year") or year
                    except Exception as cr_err:
                        logger.warning("Crossref enrichment failed for DOI %s: %s", doi, cr_err)

                title_hash = generate_title_hash(title, year)

                # Check existing publication by OpenAlex ID first, then DOI/title_hash
                existing_pub = None
                if openalex_id:
                    stmt = select(Publication).where(Publication.openalex_id == openalex_id)
                    existing_pub = (await db.execute(stmt)).scalars().first()

                if not existing_pub:
                    existing_pub = await find_existing_publication(db, doi=doi, title_hash=title_hash)

                if existing_pub:
                    # Non-destructive update: update citations, url, openalex_id
                    existing_pub.citation_count = max(existing_pub.citation_count, citations)
                    if not existing_pub.openalex_id and openalex_id:
                        existing_pub.openalex_id = openalex_id
                    if not existing_pub.doi and doi:
                        existing_pub.doi = doi
                    if not existing_pub.venue and venue:
                        existing_pub.venue = venue
                    if existing_pub.abstract == "No abstract provided in OpenAlex record." and len(abstract) > 30:
                        existing_pub.abstract = abstract
                    job.records_updated += 1
                    pub_obj = existing_pub
                else:
                    pub_obj = Publication(
                        id=uuid.uuid4(),
                        title=title,
                        abstract=abstract or "Abstract not available for this scholarly work.",
                        venue=venue,
                        publication_year=year,
                        doi=doi,
                        title_hash=title_hash,
                        citation_count=citations,
                        url=work.get("url") or openalex_id,
                        is_synthetic=False,
                        openalex_id=openalex_id,
                        crossref_id=doi,
                    )
                    db.add(pub_obj)
                    await db.flush()
                    job.records_created += 1

                # Record Provenance
                prov = EntityProvenance(
                    id=uuid.uuid4(),
                    entity_type="PUBLICATION",
                    entity_id=pub_obj.id,
                    import_job_id=job.id,
                    external_id=openalex_id or doi or title_hash,
                    raw_payload={
                        "title": title,
                        "doi": doi,
                        "openalex_id": openalex_id,
                        "venue": venue,
                        "year": year,
                        "enriched_crossref": enrich_with_crossref,
                    },
                )
                db.add(prov)

                # Link authors if matching faculty exists
                for idx, author_info in enumerate(work.get("authors", [])):
                    author_name = author_info.get("name", "Unknown Author")
                    # Check if faculty exists by name or OpenAlex ID
                    fac_stmt = select(Faculty).where(
                        (Faculty.openalex_id == author_info.get("openalex_id"))
                        | (
                            func.lower(Faculty.first_name + " " + Faculty.last_name)
                            == func.lower(author_name)
                        )
                    )
                    fac = (await db.execute(fac_stmt)).scalars().first()

                    # Avoid duplicate authorship
                    auth_stmt = select(PublicationAuthorship).where(
                        PublicationAuthorship.publication_id == pub_obj.id,
                        PublicationAuthorship.raw_author_name == author_name,
                    )
                    if not (await db.execute(auth_stmt)).scalars().first():
                        authorship = PublicationAuthorship(
                            id=uuid.uuid4(),
                            publication_id=pub_obj.id,
                            faculty_id=fac.id if fac else None,
                            author_order=idx + 1,
                            raw_author_name=author_name,
                            is_corresponding=(idx == 0),
                        )
                        db.add(authorship)

                created_pubs.append(pub_obj)

                # Auto generate vector embedding
                if auto_embed:
                    text = f"{pub_obj.title}. {pub_obj.abstract}"
                    await embedding_service.get_or_create_embedding(
                        db, "PUBLICATION", pub_obj.id, "ABSTRACT", text, force_refresh=True
                    )

            except Exception as e:
                logger.error("Error importing work %s: %s", work.get("title"), e)
                errors.append({"work_title": work.get("title"), "error": str(e)})

        job.status = "COMPLETED" if not errors else "COMPLETED_WITH_ERRORS"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        job.error_log = errors
        await db.commit()

        return {
            "job_id": str(job.id),
            "status": job.status,
            "processed": job.records_processed,
            "created": job.records_created,
            "updated": job.records_updated,
            "errors": errors,
        }

    async def import_openalex_authors(
        self,
        db: AsyncSession,
        authors_data: List[Dict[str, Any]],
        default_department: str = "Computer Science",
        default_status: str = "PENDING_REVIEW",
        auto_embed: bool = True,
    ) -> Dict[str, Any]:
        """Imports selected OpenAlex researcher/author records as unverified/pending faculty."""
        ds = await self._get_or_create_data_source(
            db, "OpenAlex Authors", "OPENALEX", "https://api.openalex.org/authors"
        )

        job = ImportJob(
            id=uuid.uuid4(),
            data_source_id=ds.id,
            status="RUNNING",
            started_at=datetime.datetime.now(datetime.timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            error_log=[],
        )
        db.add(job)
        await db.flush()

        errors = []

        for author in authors_data:
            job.records_processed += 1
            try:
                openalex_id = author.get("openalex_id") or author.get("id")
                display_name = author.get("display_name", "Unknown Researcher")
                parts = display_name.split()
                first_name = parts[0] if parts else "Unknown"
                last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

                inst_name = author.get("institution_name")
                inst_ror = author.get("institution_ror")
                topics = author.get("topics", [])
                works_count = author.get("works_count", 0)
                citations = author.get("cited_by_count", 0)

                # Check if faculty with this openalex_id already exists
                stmt = select(Faculty).where(Faculty.openalex_id == openalex_id)
                existing_fac = (await db.execute(stmt)).scalars().first()

                if existing_fac:
                    existing_fac.institution_name = inst_name or existing_fac.institution_name
                    existing_fac.institution_ror = inst_ror or existing_fac.institution_ror
                    job.records_updated += 1
                    fac_obj = existing_fac
                else:
                    # Provision placeholder user for clean foreign key mapping
                    slug_email = (
                        f"{first_name.lower()}.{last_name.lower().replace(' ', '')}."
                        f"{uuid.uuid4().hex[:4]}@openalex.faculty.internal"
                    )
                    user = User(
                        id=uuid.uuid4(),
                        email=slug_email,
                        hashed_password=get_password_hash("ImportedFacultyAuth123!"),
                        role="FACULTY",
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()

                    bio_text = (
                        f"Scholarly researcher imported from OpenAlex. "
                        f"Primary institution: {inst_name or 'Independent'}. "
                        f"Authored {works_count} publications with {citations} citations. "
                        f"Key research domains: {', '.join(topics[:5]) if topics else 'General Research'}."
                    )

                    fac_obj = Faculty(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        faculty_number=f"OALX-{uuid.uuid4().hex[:6].upper()}",
                        first_name=first_name,
                        last_name=last_name or "Researcher",
                        department=default_department,
                        title_rank="RESEARCH_SCIENTIST",
                        office_location=None,
                        website_url=openalex_id,
                        lab_name=f"{last_name or first_name} Research Group",
                        accepting_students=True,
                        max_capacity=5,
                        current_student_count=0,
                        bio=bio_text,
                        is_synthetic=False,
                        verification_status=default_status,
                        openalex_id=openalex_id,
                        institution_name=inst_name,
                        institution_ror=inst_ror,
                        verification_notes="Imported from OpenAlex. Requires institutional faculty verification.",
                    )
                    db.add(fac_obj)
                    await db.flush()
                    job.records_created += 1

                # Provenance
                prov = EntityProvenance(
                    id=uuid.uuid4(),
                    entity_type="FACULTY",
                    entity_id=fac_obj.id,
                    import_job_id=job.id,
                    external_id=openalex_id,
                    raw_payload={
                        "display_name": display_name,
                        "openalex_id": openalex_id,
                        "institution_name": inst_name,
                        "works_count": works_count,
                        "cited_by_count": citations,
                        "topics": topics,
                    },
                )
                db.add(prov)

                # Auto generate vector embedding
                if auto_embed and fac_obj.bio:
                    await embedding_service.get_or_create_embedding(
                        db,
                        "FACULTY",
                        fac_obj.id,
                        "HOLISTIC_PROFILE",
                        fac_obj.bio,
                        force_refresh=True,
                    )

            except Exception as e:
                logger.error("Error importing author %s: %s", author.get("display_name"), e)
                errors.append({"author_name": author.get("display_name"), "error": str(e)})

        job.status = "COMPLETED" if not errors else "COMPLETED_WITH_ERRORS"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        job.error_log = errors
        await db.commit()

        return {
            "job_id": str(job.id),
            "status": job.status,
            "processed": job.records_processed,
            "created": job.records_created,
            "updated": job.records_updated,
            "errors": errors,
        }

    async def import_institutional_csv_roster(
        self,
        db: AsyncSession,
        csv_text: str,
        auto_embed: bool = True,
    ) -> Dict[str, Any]:
        """Imports verified university faculty from CSV file."""
        dtos, parse_errors = csv_importer.parse_faculty_csv(csv_text)

        ds = await self._get_or_create_data_source(
            db, "Institutional CSV", "INSTITUTIONAL_CSV", "file://faculty_roster.csv"
        )

        job = ImportJob(
            id=uuid.uuid4(),
            data_source_id=ds.id,
            status="RUNNING",
            started_at=datetime.datetime.now(datetime.timezone.utc),
            records_processed=len(dtos) + len(parse_errors),
            records_created=0,
            records_updated=0,
            error_log=list(parse_errors),
        )
        db.add(job)
        await db.flush()

        for dto in dtos:
            try:
                # Find or create user
                stmt_u = select(User).where(User.email == dto.email)
                user = (await db.execute(stmt_u)).scalars().first()
                if not user:
                    user = User(
                        id=uuid.uuid4(),
                        email=dto.email,
                        hashed_password=get_password_hash("VerifiedFaculty2026!"),
                        role="FACULTY",
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()

                # Find or create faculty
                stmt_f = select(Faculty).where(
                    (Faculty.user_id == user.id)
                    | (
                        (Faculty.first_name == dto.first_name)
                        & (Faculty.last_name == dto.last_name)
                        & (Faculty.department == dto.department)
                    )
                )
                fac = (await db.execute(stmt_f)).scalars().first()

                if fac:
                    fac.department = dto.department
                    fac.title_rank = dto.title_rank
                    fac.office_location = dto.office_location
                    fac.lab_name = dto.lab_name
                    fac.verification_status = "VERIFIED"
                    fac.is_synthetic = False
                    fac.verified_at = datetime.datetime.now(datetime.timezone.utc)
                    job.records_updated += 1
                else:
                    fac = Faculty(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        faculty_number=f"INST-{uuid.uuid4().hex[:6].upper()}",
                        first_name=dto.first_name,
                        last_name=dto.last_name,
                        department=dto.department,
                        title_rank=dto.title_rank,
                        office_location=dto.office_location,
                        website_url=dto.website_url,
                        lab_name=dto.lab_name,
                        accepting_students=dto.accepting_students,
                        max_capacity=dto.max_capacity,
                        current_student_count=0,
                        bio=dto.bio or f"Faculty member in the Department of {dto.department}.",
                        is_synthetic=False,
                        verification_status="VERIFIED",
                        openalex_id=dto.openalex_id,
                        institution_name=dto.institution_name,
                        verification_notes="Verified via institutional faculty CSV roster upload.",
                        verified_at=datetime.datetime.now(datetime.timezone.utc),
                    )
                    db.add(fac)
                    await db.flush()
                    job.records_created += 1

                # Provenance
                prov = EntityProvenance(
                    id=uuid.uuid4(),
                    entity_type="FACULTY",
                    entity_id=fac.id,
                    import_job_id=job.id,
                    external_id=dto.email,
                    raw_payload=dto.model_dump(mode="json"),
                )
                db.add(prov)

                if auto_embed and fac.bio:
                    await embedding_service.get_or_create_embedding(
                        db,
                        "FACULTY",
                        fac.id,
                        "HOLISTIC_PROFILE",
                        fac.bio,
                        force_refresh=True,
                    )

            except Exception as e:
                job.error_log.append({"email": dto.email, "error": str(e)})

        job.status = "COMPLETED" if not job.error_log else "COMPLETED_WITH_ERRORS"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        await db.commit()

        return {
            "job_id": str(job.id),
            "status": job.status,
            "processed": job.records_processed,
            "created": job.records_created,
            "updated": job.records_updated,
            "errors": job.error_log,
        }

    async def get_data_summary(self, db: AsyncSession) -> Dict[str, Any]:
        """Provides counts of real vs synthetic records and verification status breakdown."""
        # Faculty breakdown
        fac_real = (
            await db.execute(
                select(func.count(Faculty.id)).where(Faculty.is_synthetic == False)
            )
        ).scalar() or 0

        fac_synth = (
            await db.execute(
                select(func.count(Faculty.id)).where(Faculty.is_synthetic == True)
            )
        ).scalar() or 0

        # Verification status breakdown
        status_stmt = (
            select(Faculty.verification_status, func.count(Faculty.id))
            .group_by(Faculty.verification_status)
        )
        status_res = (await db.execute(status_stmt)).all()
        by_verification = {row[0]: row[1] for row in status_res}

        # Publications breakdown
        pub_real = (
            await db.execute(
                select(func.count(Publication.id)).where(Publication.is_synthetic == False)
            )
        ).scalar() or 0

        pub_synth = (
            await db.execute(
                select(func.count(Publication.id)).where(Publication.is_synthetic == True)
            )
        ).scalar() or 0

        return {
            "faculty": {
                "real_count": fac_real,
                "synthetic_count": fac_synth,
                "total": fac_real + fac_synth,
                "by_verification_status": by_verification,
            },
            "publications": {
                "real_count": pub_real,
                "synthetic_count": pub_synth,
                "total": pub_real + pub_synth,
            },
        }


real_research_data_service = RealResearchDataService()
