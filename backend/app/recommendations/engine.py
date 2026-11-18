import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.embeddings.service import embedding_service
from backend.app.models.embedding import EmbeddingRecord
from backend.app.models.faculty import Faculty
from backend.app.models.project import AcademicProject
from backend.app.models.publication import Publication, PublicationAuthorship
from backend.app.models.recommendation import RecommendationResult, RecommendationRun
from backend.app.models.student import Student
from backend.app.recommendations.schemas import (
    PublicationEvidence,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationWeights,
    ScoreBreakdown,
)
from backend.app.recommendations.scoring import (
    aggregate_top_k_publications,
    compute_cosine_similarity,
    compute_project_similarity,
    compute_skill_compatibility,
    generate_explanation_summary,
)


class RecommendationEngine:
    algorithm_version = "v1.0-hybrid-provisional"

    async def generate_recommendations(
        self,
        db: AsyncSession,
        request: RecommendationRequest,
    ) -> RecommendationResponse:
        start_time = time.perf_counter()

        # 1. Fetch Student with Details
        stmt = (
            select(Student)
            .where(Student.id == request.student_id)
            .options(
                selectinload(Student.skills_interests),
                selectinload(Student.academic_projects),
            )
        )
        student = (await db.execute(stmt)).scalars().first()
        if not student:
            raise EntityNotFoundException("Student", request.student_id)

        # 2. Fetch Candidate Faculty
        fac_stmt = (
            select(Faculty)
            .options(
                selectinload(Faculty.skills_expertise),
                selectinload(Faculty.authorship_links).selectinload(PublicationAuthorship.publication),
            )
        )
        if request.filters:
            if request.filters.departments:
                fac_stmt = fac_stmt.where(Faculty.department.in_(request.filters.departments))
            if request.filters.only_accepting_students:
                fac_stmt = fac_stmt.where(Faculty.accepting_students == True)
            if request.filters.min_capacity:
                fac_stmt = fac_stmt.where(
                    (Faculty.max_capacity - Faculty.current_student_count) >= request.filters.min_capacity
                )
            if request.filters.data_mode == "REAL_ONLY":
                fac_stmt = fac_stmt.where(Faculty.is_synthetic == False)
            elif request.filters.data_mode == "SYNTHETIC_ONLY":
                fac_stmt = fac_stmt.where(Faculty.is_synthetic == True)
            if request.filters.verified_only:
                fac_stmt = fac_stmt.where(Faculty.verification_status == "VERIFIED")

        candidate_faculty = list((await db.execute(fac_stmt)).scalars().all())

        publications_by_id = {
            link.publication.id: link.publication
            for faculty in candidate_faculty
            for link in faculty.authorship_links
            if link.publication
        }
        embedding_entity_ids = {
            student.id,
            *(project.id for project in student.academic_projects),
            *(faculty.id for faculty in candidate_faculty),
            *publications_by_id,
        }
        embedding_stmt = select(EmbeddingRecord).where(
            EmbeddingRecord.entity_id.in_(embedding_entity_ids),
            EmbeddingRecord.model_version == embedding_service.model_version,
        )
        embedding_records = list((await db.execute(embedding_stmt)).scalars().all())
        embeddings_by_key = {
            (record.entity_type, record.entity_id, record.embedding_type): record
            for record in embedding_records
        }

        async def get_embedding(
            entity_type: str,
            entity_id: uuid.UUID,
            embedding_type: str,
            source_text: str,
        ) -> Optional[EmbeddingRecord]:
            key = (entity_type, entity_id, embedding_type)
            record = embeddings_by_key.get(key)
            if record:
                return record
            record = await embedding_service.get_or_create_embedding(
                db, entity_type, entity_id, embedding_type, source_text
            )
            if record:
                embeddings_by_key[key] = record
            return record

        # 3. Get / Generate Student and Project Embeddings
        stu_emb_rec = await get_embedding(
            "STUDENT",
            student.id,
            "STATEMENT",
            f"{student.statement_of_purpose} {student.bio or ''}",
        )
        stu_vec = stu_emb_rec.vector if stu_emb_rec else None

        student_projects_with_vec: List[Tuple[AcademicProject, Optional[List[float]]]] = []
        for proj in student.academic_projects:
            p_rec = await get_embedding(
                "PROJECT", proj.id, "STATEMENT", f"{proj.title}: {proj.description}"
            )
            student_projects_with_vec.append((proj, p_rec.vector if p_rec else None))

        weights_cfg = request.weights or RecommendationWeights()

        scored_candidates: List[RecommendationItem] = []

        for fac in candidate_faculty:
            caveats: List[str] = []
            active_signals = [
                "research_interest",
                "project_research",
                "publication_relevance",
                "skill_compatibility",
            ]

            # 4a. Faculty Profile Embedding
            fac_emb_rec = await get_embedding(
                "FACULTY",
                fac.id,
                "HOLISTIC_PROFILE",
                f"{fac.bio or ''} {fac.lab_name or ''}",
            )
            fac_vec = fac_emb_rec.vector if fac_emb_rec else None

            # 4b. Faculty Publications & Embeddings
            fac_pubs_with_vec: List[Tuple[Publication, Optional[List[float]]]] = []
            for link in fac.authorship_links:
                if link.publication:
                    pub_rec = await get_embedding(
                        "PUBLICATION",
                        link.publication.id,
                        "ABSTRACT",
                        f"{link.publication.title}. {link.publication.abstract}",
                    )
                    fac_pubs_with_vec.append(
                        (link.publication, pub_rec.vector if pub_rec else None)
                    )

            # --- Signal 1: Research Interest Similarity ---
            research_score = compute_cosine_similarity(stu_vec, fac_vec)
            if not stu_vec or not fac_vec:
                active_signals.remove("research_interest")
                caveats.append("Research-profile similarity is unavailable for this profile pair")

            # --- Signal 2: Project / Research Similarity ---
            if not student_projects_with_vec:
                project_score = 0.0
                active_signals.remove("project_research")
                caveats.append("Student profile does not include past projects; project signal re-weighted")
            elif not fac_pubs_with_vec:
                project_score = 0.0
                active_signals.remove("project_research")
            else:
                project_score = compute_project_similarity(student_projects_with_vec, fac_pubs_with_vec)

            # --- Signal 3: Publication Relevance (Aggregated top-K) ---
            if not stu_vec or not fac_pubs_with_vec:
                pub_score = 0.0
                top_pubs = []
                if "publication_relevance" in active_signals:
                    active_signals.remove("publication_relevance")
                if not fac_pubs_with_vec:
                    caveats.append("Faculty has no publications indexed; publication signals re-weighted")
                else:
                    caveats.append("Student research statement is unavailable for publication matching")
            else:
                pub_score, top_pubs = aggregate_top_k_publications(stu_vec, fac_pubs_with_vec, top_k=3)

            # --- Signal 4: Skill Compatibility ---
            skill_score, shared_skills = compute_skill_compatibility(
                student.skills_interests, fac.skills_expertise
            )
            if not student.skills_interests or not fac.skills_expertise:
                active_signals.remove("skill_compatibility")
                caveats.append("Limited skill overlap data available")

            # Dynamic weight re-normalization over active signals
            norm_weights = weights_cfg.normalized(active_signals)

            overall_score = (
                norm_weights.get("research_interest", 0.0) * research_score
                + norm_weights.get("project_research", 0.0) * project_score
                + norm_weights.get("publication_relevance", 0.0) * pub_score
                + norm_weights.get("skill_compatibility", 0.0) * skill_score
            )
            overall_score = round(float(overall_score), 4)

            faculty_name = f"{fac.first_name} {fac.last_name}"
            explanation = generate_explanation_summary(
                faculty_name=faculty_name,
                lab_name=fac.lab_name,
                research_score=research_score,
                skill_score=skill_score,
                shared_skills=shared_skills,
                top_pubs=top_pubs,
                caveats=caveats,
                research_data_available=bool(stu_vec and fac_vec),
            )

            open_capacity = max(0, fac.max_capacity - fac.current_student_count)

            scored_candidates.append(
                RecommendationItem(
                    faculty_id=fac.id,
                    faculty_name=faculty_name,
                    department=fac.department,
                    title_rank=fac.title_rank,
                    lab_name=fac.lab_name,
                    accepting_students=fac.accepting_students,
                    open_capacity=open_capacity,
                    rank_position=0,  # Assigned after sorting
                    overall_score=overall_score,
                    score_breakdown=ScoreBreakdown(
                        research_interest_score=research_score,
                        project_research_score=project_score,
                        publication_relevance_score=pub_score,
                        skill_compatibility_score=skill_score,
                        normalized_weights=norm_weights,
                    ),
                    top_publications=top_pubs,
                    shared_skills=shared_skills,
                    explanation_summary=explanation,
                    missing_data_caveats=caveats,
                    is_synthetic=fac.is_synthetic,
                    verification_status=fac.verification_status,
                    openalex_id=fac.openalex_id,
                    institution_name=fac.institution_name,
                )
            )

        # 5. Sort Descending by Overall Score
        scored_candidates.sort(key=lambda x: x.overall_score, reverse=True)

        top_recommendations = scored_candidates[: request.top_k]
        for rank, item in enumerate(top_recommendations, start=1):
            item.rank_position = rank

        execution_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 6. Save Recommendation Run & Results for Auditing
        run = RecommendationRun(
            id=uuid.uuid4(),
            student_id=student.id,
            algorithm_version=self.algorithm_version,
            parameters={
                "top_k": request.top_k,
                "weights": weights_cfg.model_dump(),
                "filters": request.filters.model_dump() if request.filters else {},
            },
            execution_time_ms=execution_ms,
        )
        db.add(run)
        await db.flush()

        for rec_item in top_recommendations:
            res_row = RecommendationResult(
                id=uuid.uuid4(),
                run_id=run.id,
                faculty_id=rec_item.faculty_id,
                rank_position=rec_item.rank_position,
                overall_score=rec_item.overall_score,
                semantic_score=rec_item.score_breakdown.research_interest_score,
                skill_score=rec_item.score_breakdown.skill_compatibility_score,
                project_score=rec_item.score_breakdown.project_research_score,
                explanation_data={
                    "score_breakdown": rec_item.score_breakdown.model_dump(),
                    "top_publications": [p.model_dump(mode="json") for p in rec_item.top_publications],
                    "shared_skills": rec_item.shared_skills,
                    "explanation_summary": rec_item.explanation_summary,
                    "missing_data_caveats": rec_item.missing_data_caveats,
                },
            )
            db.add(res_row)

        await db.commit()

        return RecommendationResponse(
            run_id=run.id,
            student_id=student.id,
            algorithm_version=self.algorithm_version,
            execution_time_ms=execution_ms,
            total_candidates_evaluated=len(candidate_faculty),
            recommendations=top_recommendations,
        )


recommendation_engine = RecommendationEngine()
