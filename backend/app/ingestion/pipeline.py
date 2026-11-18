import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.logging import logger
from backend.app.ingestion.deduplication import (
    find_existing_publication,
    find_existing_topic,
    find_existing_user,
)
from backend.app.ingestion.schemas import BatchIngestPayload
from backend.app.models.evaluation import RelevanceJudgment
from backend.app.models.embedding import EmbeddingRecord
from backend.app.models.faculty import Faculty
from backend.app.models.project import AcademicProject, project_skills
from backend.app.models.provenance import DataSource, EntityProvenance, ImportJob
from backend.app.models.publication import Publication, PublicationAuthorship
from backend.app.models.student import Student
from backend.app.models.taxonomy import (
    FacultySkillExpertise,
    StudentSkillInterest,
    TopicSkill,
)
from backend.app.models.user import User


class IngestionPipeline:
    async def get_or_create_data_source(
        self,
        db: AsyncSession,
        name: str,
        source_type: str,
        base_url: Optional[str] = None,
    ) -> DataSource:
        stmt = select(DataSource).where(DataSource.name == name)
        res = await db.execute(stmt)
        source = res.scalars().first()
        if not source:
            source = DataSource(
                id=uuid.uuid4(),
                name=name,
                source_type=source_type,
                base_url=base_url,
                is_active=True,
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)
        return source

    async def ingest_batch(
        self,
        db: AsyncSession,
        payload: BatchIngestPayload,
        source_name: str = "synthetic_generator",
        source_type: str = "SYNTHETIC",
    ) -> ImportJob:
        data_source = await self.get_or_create_data_source(
            db, name=source_name, source_type=source_type
        )

        job = ImportJob(
            id=uuid.uuid4(),
            data_source_id=data_source.id,
            status="RUNNING",
            records_processed=0,
            records_created=0,
            records_updated=0,
            error_log=[],
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        topic_map: Dict[str, TopicSkill] = {}
        faculty_email_map: Dict[str, Faculty] = {}
        student_email_map: Dict[str, Student] = {}

        try:
            # 1. Ingest Topics and Skills (sorted: roots first)
            sorted_topics = sorted(
                payload.topics, key=lambda t: 0 if t.parent_slug is None else 1
            )
            for topic_dto in sorted_topics:
                job.records_processed += 1
                existing_topic = await find_existing_topic(
                    db, slug=topic_dto.slug, name=topic_dto.name
                )
                parent_id = None
                if topic_dto.parent_slug and topic_dto.parent_slug in topic_map:
                    parent_id = topic_map[topic_dto.parent_slug].id

                if existing_topic:
                    if parent_id and not existing_topic.parent_id:
                        existing_topic.parent_id = parent_id
                    topic_map[existing_topic.slug] = existing_topic
                    job.records_updated += 1
                else:
                    new_topic = TopicSkill(
                        id=uuid.uuid4(),
                        name=topic_dto.name,
                        slug=topic_dto.slug,
                        category=topic_dto.category,
                        parent_id=parent_id,
                        description=topic_dto.description,
                    )
                    db.add(new_topic)
                    await db.flush()
                    topic_map[new_topic.slug] = new_topic
                    job.records_created += 1

                    # Provenance
                    prov = EntityProvenance(
                        id=uuid.uuid4(),
                        entity_type="TOPIC",
                        entity_id=new_topic.id,
                        import_job_id=job.id,
                        external_id=topic_dto.slug,
                        raw_payload=topic_dto.model_dump(mode="json"),
                    )
                    db.add(prov)

            # 2. Ingest Faculty Members
            for fac_dto in payload.faculty:
                job.records_processed += 1
                existing_user = await find_existing_user(db, fac_dto.email)
                if not existing_user:
                    user = User(
                        id=uuid.uuid4(),
                        email=fac_dto.email.lower().strip(),
                        hashed_password="synthetic_password_hash",
                        role="FACULTY",
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()
                else:
                    user = existing_user

                stmt = select(Faculty).where(Faculty.user_id == user.id)
                res = await db.execute(stmt)
                faculty = res.scalars().first()

                if not faculty:
                    faculty = Faculty(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        faculty_number=f"SYNTH-FAC-{uuid.uuid4().hex[:6].upper()}",
                        first_name=fac_dto.first_name,
                        last_name=fac_dto.last_name,
                        department=fac_dto.department,
                        title_rank=fac_dto.title_rank,
                        office_location=fac_dto.office_location,
                        website_url=fac_dto.website_url,
                        lab_name=fac_dto.lab_name,
                        accepting_students=fac_dto.accepting_students,
                        max_capacity=fac_dto.max_capacity,
                        current_student_count=fac_dto.current_student_count,
                        bio=fac_dto.bio,
                        is_synthetic=fac_dto.is_synthetic,
                        verification_status=fac_dto.verification_status,
                        openalex_id=fac_dto.openalex_id,
                        institution_name=fac_dto.institution_name,
                        institution_ror=fac_dto.institution_ror,
                        verification_notes=fac_dto.verification_notes,
                    )
                    db.add(faculty)
                    await db.flush()
                    job.records_created += 1

                    prov = EntityProvenance(
                        id=uuid.uuid4(),
                        entity_type="FACULTY",
                        entity_id=faculty.id,
                        import_job_id=job.id,
                        external_id=fac_dto.email,
                        raw_payload=fac_dto.model_dump(mode="json"),
                    )
                    db.add(prov)
                else:
                    faculty.first_name = fac_dto.first_name
                    faculty.last_name = fac_dto.last_name
                    faculty.department = fac_dto.department
                    faculty.lab_name = fac_dto.lab_name
                    faculty.accepting_students = fac_dto.accepting_students
                    job.records_updated += 1

                faculty_email_map[fac_dto.email.lower()] = faculty

                # Attach Faculty Skills
                for skill_dto in fac_dto.skills:
                    if skill_dto.topic_slug in topic_map:
                        t_id = topic_map[skill_dto.topic_slug].id
                        check_stmt = select(FacultySkillExpertise).where(
                            FacultySkillExpertise.faculty_id == faculty.id,
                            FacultySkillExpertise.topic_skill_id == t_id,
                        )
                        ex = (await db.execute(check_stmt)).scalars().first()
                        if not ex:
                            fac_skill = FacultySkillExpertise(
                                id=uuid.uuid4(),
                                faculty_id=faculty.id,
                                topic_skill_id=t_id,
                                expertise_level=skill_dto.expertise_level,
                                is_primary_focus=skill_dto.is_primary_focus,
                            )
                            db.add(fac_skill)

            # 3. Ingest Students
            for stu_dto in payload.students:
                job.records_processed += 1
                existing_user = await find_existing_user(db, stu_dto.email)
                if not existing_user:
                    user = User(
                        id=uuid.uuid4(),
                        email=stu_dto.email.lower().strip(),
                        hashed_password="synthetic_password_hash",
                        role="STUDENT",
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()
                else:
                    user = existing_user

                stmt = select(Student).where(Student.user_id == user.id)
                res = await db.execute(stmt)
                student = res.scalars().first()

                if not student:
                    student = Student(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        student_number=f"SYNTH-STU-{uuid.uuid4().hex[:6].upper()}",
                        first_name=stu_dto.first_name,
                        last_name=stu_dto.last_name,
                        department=stu_dto.department,
                        degree_level=stu_dto.degree_level,
                        gpa_or_standing=stu_dto.gpa_or_standing,
                        graduation_year=stu_dto.graduation_year,
                        bio=stu_dto.bio,
                        statement_of_purpose=stu_dto.statement_of_purpose,
                        availability_status=stu_dto.availability_status,
                    )
                    db.add(student)
                    await db.flush()
                    job.records_created += 1

                    prov = EntityProvenance(
                        id=uuid.uuid4(),
                        entity_type="STUDENT",
                        entity_id=student.id,
                        import_job_id=job.id,
                        external_id=stu_dto.email,
                        raw_payload=stu_dto.model_dump(mode="json"),
                    )
                    db.add(prov)
                else:
                    student.first_name = stu_dto.first_name
                    student.last_name = stu_dto.last_name
                    student.statement_of_purpose = stu_dto.statement_of_purpose
                    job.records_updated += 1

                student_email_map[stu_dto.email.lower()] = student

                # Attach Student Skills
                for skill_dto in stu_dto.skills:
                    if skill_dto.topic_slug in topic_map:
                        t_id = topic_map[skill_dto.topic_slug].id
                        check_stmt = select(StudentSkillInterest).where(
                            StudentSkillInterest.student_id == student.id,
                            StudentSkillInterest.topic_skill_id == t_id,
                        )
                        ex = (await db.execute(check_stmt)).scalars().first()
                        if not ex:
                            stu_skill = StudentSkillInterest(
                                id=uuid.uuid4(),
                                student_id=student.id,
                                topic_skill_id=t_id,
                                proficiency_level=skill_dto.proficiency_level,
                                interest_level=skill_dto.interest_level,
                                years_experience=skill_dto.years_experience,
                            )
                            db.add(stu_skill)

                # Ingest Projects
                for proj_dto in stu_dto.projects:
                    proj = AcademicProject(
                        id=uuid.uuid4(),
                        student_id=student.id,
                        title=proj_dto.title,
                        description=proj_dto.description,
                        role=proj_dto.role,
                        start_date=proj_dto.start_date,
                        end_date=proj_dto.end_date,
                        github_url=proj_dto.github_url,
                    )
                    db.add(proj)
                    await db.flush()

                    for slug in proj_dto.skill_slugs:
                        if slug in topic_map:
                            t_id = topic_map[slug].id
                            await db.execute(
                                project_skills.insert().values(
                                    project_id=proj.id, topic_skill_id=t_id
                                )
                            )

            # 4. Ingest Publications with Deduplication
            for pub_dto in payload.publications:
                job.records_processed += 1
                existing_pub = await find_existing_publication(
                    db, doi=pub_dto.doi, title_hash=pub_dto.title_hash
                )

                if existing_pub:
                    publication = existing_pub
                    job.records_updated += 1
                else:
                    publication = Publication(
                        id=uuid.uuid4(),
                        title=pub_dto.title,
                        abstract=pub_dto.abstract,
                        venue=pub_dto.venue,
                        publication_year=pub_dto.publication_year,
                        doi=pub_dto.doi,
                        pmid=pub_dto.pmid,
                        arxiv_id=pub_dto.arxiv_id,
                        title_hash=pub_dto.title_hash,
                        citation_count=pub_dto.citation_count,
                        url=pub_dto.url,
                        is_synthetic=pub_dto.is_synthetic,
                        openalex_id=pub_dto.openalex_id,
                        crossref_id=pub_dto.crossref_id,
                        is_retracted=pub_dto.is_retracted,
                    )
                    db.add(publication)
                    await db.flush()
                    job.records_created += 1

                    prov = EntityProvenance(
                        id=uuid.uuid4(),
                        entity_type="PUBLICATION",
                        entity_id=publication.id,
                        import_job_id=job.id,
                        external_id=pub_dto.doi or pub_dto.title_hash,
                        raw_payload=pub_dto.model_dump(mode="json"),
                    )
                    db.add(prov)

                # Link Authors
                author_names = pub_dto.author_names or ["Anonymous Researcher"]
                for idx, author_name in enumerate(author_names, start=1):
                    fac_ref = None
                    if idx <= len(pub_dto.author_faculty_emails):
                        fac_email = pub_dto.author_faculty_emails[idx - 1].lower()
                        fac_ref = faculty_email_map.get(fac_email)

                    fac_id = fac_ref.id if fac_ref else None

                    # Deduplicate authorship link
                    auth_stmt = select(PublicationAuthorship).where(
                        PublicationAuthorship.publication_id == publication.id,
                        PublicationAuthorship.faculty_id == fac_id,
                    )
                    existing_auth = (await db.execute(auth_stmt)).scalars().first()
                    if not existing_auth:
                        auth = PublicationAuthorship(
                            id=uuid.uuid4(),
                            publication_id=publication.id,
                            faculty_id=fac_id,
                            author_order=idx,
                            raw_author_name=author_name,
                            is_corresponding=(idx == 1),
                        )
                        db.add(auth)

            # 5. Ingest Benchmark Relevance Judgments
            seen_in_batch = set()
            for rj_dto in payload.relevance_judgments:
                stu = student_email_map.get(rj_dto.student_email.lower())
                fac = faculty_email_map.get(rj_dto.faculty_email.lower())
                if stu and fac:
                    batch_key = (stu.id, fac.id, rj_dto.benchmark_suite)
                    if batch_key in seen_in_batch:
                        continue
                    seen_in_batch.add(batch_key)

                    job.records_processed += 1
                    rj_stmt = select(RelevanceJudgment).where(
                        RelevanceJudgment.student_id == stu.id,
                        RelevanceJudgment.faculty_id == fac.id,
                        RelevanceJudgment.benchmark_suite == rj_dto.benchmark_suite,
                    )
                    existing_rj = (await db.execute(rj_stmt)).scalars().first()
                    if not existing_rj:
                        rj = RelevanceJudgment(
                            id=uuid.uuid4(),
                            student_id=stu.id,
                            faculty_id=fac.id,
                            benchmark_suite=rj_dto.benchmark_suite,
                            relevance_grade=rj_dto.relevance_grade,
                            annotator_id=rj_dto.annotator_id,
                            notes=rj_dto.notes,
                        )
                        db.add(rj)
                        job.records_created += 1

            job.status = "COMPLETED"
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(job)
            logger.info(
                f"Ingestion completed for job {job.id}. Processed={job.records_processed}, Created={job.records_created}, Updated={job.records_updated}."
            )
            return job

        except Exception as exc:
            import traceback
            traceback.print_exc()
            await db.rollback()
            logger.error(f"Ingestion job {job.id} failed: {exc}", exc_info=True)
            raise

    async def reset_synthetic_data(self, db: AsyncSession) -> Dict[str, int]:
        """Safely removes all records originating from SYNTHETIC data sources.
        Guarantees that real academic data or other sources are completely preserved.
        """
        # Find synthetic data sources
        stmt = select(DataSource.id).where(DataSource.source_type == "SYNTHETIC")
        res = await db.execute(stmt)
        synthetic_source_ids = list(res.scalars().all())

        if not synthetic_source_ids:
            return {"deleted_entities": 0}

        # Find import jobs for synthetic data sources
        job_stmt = select(ImportJob.id).where(ImportJob.data_source_id.in_(synthetic_source_ids))
        job_res = await db.execute(job_stmt)
        synthetic_job_ids = list(job_res.scalars().all())

        # Find provenance records
        prov_stmt = select(EntityProvenance).where(EntityProvenance.import_job_id.in_(synthetic_job_ids))
        prov_res = await db.execute(prov_stmt)
        provenance_records = list(prov_res.scalars().all())

        # Collect entity IDs to delete
        student_ids = [p.entity_id for p in provenance_records if p.entity_type == "STUDENT"]
        faculty_ids = [p.entity_id for p in provenance_records if p.entity_type == "FACULTY"]
        pub_ids = [p.entity_id for p in provenance_records if p.entity_type == "PUBLICATION"]
        topic_ids = [p.entity_id for p in provenance_records if p.entity_type == "TOPIC"]

        deleted_counts = {
            "students": len(student_ids),
            "faculty": len(faculty_ids),
            "publications": len(pub_ids),
            "topics": len(topic_ids),
        }

        # Delete associated embeddings for synthetic entities
        all_entity_ids = list(student_ids) + list(faculty_ids) + list(pub_ids)
        if student_ids:
            proj_stmt = select(AcademicProject.id).where(AcademicProject.student_id.in_(student_ids))
            proj_ids = list((await db.execute(proj_stmt)).scalars().all())
            all_entity_ids.extend(proj_ids)
        if all_entity_ids:
            await db.execute(delete(EmbeddingRecord).where(EmbeddingRecord.entity_id.in_(all_entity_ids)))

        # Delete students (cascades to user and projects)
        if student_ids:
            # Get user IDs for students
            user_stmt = select(Student.user_id).where(Student.id.in_(student_ids))
            user_ids = list((await db.execute(user_stmt)).scalars().all())
            await db.execute(delete(Student).where(Student.id.in_(student_ids)))
            if user_ids:
                await db.execute(delete(User).where(User.id.in_(user_ids)))

        # Delete faculty (cascades to user)
        if faculty_ids:
            user_stmt = select(Faculty.user_id).where(Faculty.id.in_(faculty_ids))
            user_ids = list((await db.execute(user_stmt)).scalars().all())
            await db.execute(delete(Faculty).where(Faculty.id.in_(faculty_ids)))
            if user_ids:
                await db.execute(delete(User).where(User.id.in_(user_ids)))

        # Delete publications
        if pub_ids:
            await db.execute(delete(Publication).where(Publication.id.in_(pub_ids)))

        # Delete topics
        if topic_ids:
            await db.execute(delete(TopicSkill).where(TopicSkill.id.in_(topic_ids)))

        # Delete import jobs
        if synthetic_job_ids:
            await db.execute(delete(ImportJob).where(ImportJob.id.in_(synthetic_job_ids)))

        await db.commit()
        logger.info(f"Synthetic data reset completed: {deleted_counts}")
        return deleted_counts


ingestion_pipeline = IngestionPipeline()
