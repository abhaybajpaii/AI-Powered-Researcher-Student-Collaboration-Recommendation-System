from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.ingestion.pipeline import ingestion_pipeline
from backend.app.ingestion.schemas import BatchIngestPayload
from backend.app.models.evaluation import RelevanceJudgment
from backend.app.models.faculty import Faculty
from backend.app.models.provenance import DataSource, EntityProvenance, ImportJob
from backend.app.models.publication import Publication
from backend.app.models.student import Student
from backend.app.models.taxonomy import TopicSkill
from backend.app.models.user import User
from backend.app.schemas.common import PaginatedResponse, PaginationParams
from backend.app.synthetic.generator import SyntheticConfig, SyntheticDataGenerator


class AdminService:
    async def seed_synthetic_dataset(
        self,
        db: AsyncSession,
        config: Optional[SyntheticConfig] = None,
        reset_existing: bool = False,
    ) -> Dict[str, Any]:
        """Generates and ingests a synthetic dataset with optional safe reset of previous synthetic records."""
        config = config or SyntheticConfig()

        reset_summary = {}
        if reset_existing:
            reset_summary = await ingestion_pipeline.reset_synthetic_data(db)

        generator = SyntheticDataGenerator(config=config)
        payload = generator.generate()

        job = await ingestion_pipeline.ingest_batch(
            db, payload=payload, source_name="synthetic_generator", source_type="SYNTHETIC"
        )

        return {
            "job_id": job.id,
            "status": job.status,
            "records_processed": job.records_processed,
            "records_created": job.records_created,
            "records_updated": job.records_updated,
            "config": config.model_dump(),
            "reset_summary": reset_summary,
        }

    async def reset_synthetic_data(self, db: AsyncSession) -> Dict[str, Any]:
        """Safely removes all records originating from SYNTHETIC data sources."""
        deleted = await ingestion_pipeline.reset_synthetic_data(db)
        return {"status": "success", "deleted": deleted}

    async def list_import_jobs(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
    ) -> PaginatedResponse[Dict[str, Any]]:
        stmt = (
            select(ImportJob, DataSource.name.label("source_name"), DataSource.source_type)
            .join(DataSource, ImportJob.data_source_id == DataSource.id)
            .order_by(ImportJob.started_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        res = await db.execute(stmt)
        rows = res.all()

        count_stmt = select(func.count(ImportJob.id))
        total = (await db.execute(count_stmt)).scalar() or 0

        items = [
            {
                "id": job.id,
                "data_source_id": job.data_source_id,
                "data_source_name": source_name,
                "data_source_type": source_type,
                "status": job.status,
                "records_processed": job.records_processed,
                "records_created": job.records_created,
                "records_updated": job.records_updated,
                "error_log": job.error_log,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
            }
            for job, source_name, source_type in rows
        ]

        return PaginatedResponse.create(items=items, total=total, params=pagination)

    async def get_import_job(self, db: AsyncSession, job_id: UUID) -> Dict[str, Any]:
        stmt = (
            select(ImportJob, DataSource.name.label("source_name"), DataSource.source_type)
            .join(DataSource, ImportJob.data_source_id == DataSource.id)
            .where(ImportJob.id == job_id)
        )
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            raise EntityNotFoundException("ImportJob", job_id)

        job, source_name, source_type = row
        return {
            "id": job.id,
            "data_source_id": job.data_source_id,
            "data_source_name": source_name,
            "data_source_type": source_type,
            "status": job.status,
            "records_processed": job.records_processed,
            "records_created": job.records_created,
            "records_updated": job.records_updated,
            "error_log": job.error_log,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }

    async def get_data_counts(self, db: AsyncSession) -> Dict[str, Any]:
        """Returns entity counts broken down by data mode (synthetic vs other/real)."""
        # Count total entities
        total_students = (await db.execute(select(func.count(Student.id)))).scalar() or 0
        total_faculty = (await db.execute(select(func.count(Faculty.id)))).scalar() or 0
        total_publications = (await db.execute(select(func.count(Publication.id)))).scalar() or 0
        total_topics = (await db.execute(select(func.count(TopicSkill.id)))).scalar() or 0
        total_relevance = (await db.execute(select(func.count(RelevanceJudgment.id)))).scalar() or 0

        # Count synthetic provenance entities
        synth_stmt = (
            select(EntityProvenance.entity_type, func.count(EntityProvenance.id))
            .join(ImportJob, EntityProvenance.import_job_id == ImportJob.id)
            .join(DataSource, ImportJob.data_source_id == DataSource.id)
            .where(DataSource.source_type == "SYNTHETIC")
            .group_by(EntityProvenance.entity_type)
        )
        synth_res = await db.execute(synth_stmt)
        synth_map = dict(synth_res.all())

        synthetic_students = synth_map.get("STUDENT", 0)
        synthetic_faculty = synth_map.get("FACULTY", 0)
        synthetic_pubs = synth_map.get("PUBLICATION", 0)
        synthetic_topics = synth_map.get("TOPIC", 0)

        return {
            "summary": {
                "total_records": total_students + total_faculty + total_publications + total_topics + total_relevance,
                "synthetic_records": synthetic_students + synthetic_faculty + synthetic_pubs + synthetic_topics,
                "real_records": (total_students - synthetic_students) + (total_faculty - synthetic_faculty) + (total_publications - synthetic_pubs),
            },
            "by_entity": {
                "students": {"total": total_students, "synthetic": synthetic_students, "real": max(0, total_students - synthetic_students)},
                "faculty": {"total": total_faculty, "synthetic": synthetic_faculty, "real": max(0, total_faculty - synthetic_faculty)},
                "publications": {"total": total_publications, "synthetic": synthetic_pubs, "real": max(0, total_publications - synthetic_pubs)},
                "topics_and_skills": {"total": total_topics, "synthetic": synthetic_topics, "real": max(0, total_topics - synthetic_topics)},
                "relevance_judgments": {"total": total_relevance, "synthetic": total_relevance, "real": 0},
            },
        }

    def validate_batch(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validates an inbound batch payload against Pydantic Ingestion schemas without DB insertion."""
        try:
            parsed = BatchIngestPayload.model_validate(raw_payload)
            return {
                "valid": True,
                "summary": {
                    "topics": len(parsed.topics),
                    "faculty": len(parsed.faculty),
                    "students": len(parsed.students),
                    "publications": len(parsed.publications),
                    "relevance_judgments": len(parsed.relevance_judgments),
                },
                "errors": [],
            }
        except Exception as exc:
            return {
                "valid": False,
                "summary": {},
                "errors": [str(exc)],
            }


admin_service = AdminService()
