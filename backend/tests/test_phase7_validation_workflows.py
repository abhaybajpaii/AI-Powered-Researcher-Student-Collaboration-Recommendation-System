"""Phase 7 Final End-to-End Validation Workflows.

Tests:
- Workflow A: Synthetic Demonstration
  1. Generate synthetic data via admin endpoint
  2. Create/update a student profile
  3. Generate recommendations
  4. Inspect grounded evidence and multi-signal score breakdown
  5. Run offline IR benchmark evaluation (NDCG@K, Precision@K, Recall@K, MRR)

- Workflow B: Real Research Data
  1. Ingest scholarly OpenAlex works with abstract reconstruction
  2. Ingest OpenAlex researchers (tagged PENDING_REVIEW)
  3. Ingest institutional CSV faculty roster (tagged VERIFIED)
  4. Verify provenance tracking and deduplication
  5. Generate dense vector embeddings for real records
  6. Produce recommendations based on REAL_ONLY mode
  7. Verify verification status labeling and verified_only filter
"""

import uuid
from typing import Any, Dict
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.faculty import Faculty
from backend.app.models.provenance import EntityProvenance, ImportJob
from backend.app.models.publication import Publication
from backend.app.models.student import Student
from backend.app.models.user import User


@pytest.mark.asyncio
class TestPhase7WorkflowA_Synthetic:
    """Workflow A: Synthetic Demonstration Validation."""

    async def test_workflow_a_complete_synthetic_cycle(
        self, client: AsyncClient, db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ):
        admin_headers = admin_auth_headers

        # 1. Generate & Seed synthetic dataset
        seed_res = await client.post(
            "/api/v1/admin/seed-synthetic",
            json={"num_students": 15, "num_faculty": 10, "num_publications": 25, "seed": 42},
            headers=admin_headers,
        )
        assert seed_res.status_code == 200
        seed_data = seed_res.json()
        assert seed_data["status"] == "COMPLETED"

        # Verify synthetic records exist in DB
        stud_stmt = select(Student).where(Student.is_synthetic == True)
        students = (await db_session.execute(stud_stmt)).scalars().all()
        assert len(students) >= 15
        test_student = students[0]

        # 2. Sync embeddings
        sync_res = await client.post(
            "/api/v1/embeddings/sync", headers=admin_headers
        )
        assert sync_res.status_code == 200
        sync_data = sync_res.json()
        assert sync_data["status"] == "sync_complete"

        # 3. Generate recommendations for student
        rec_res = await client.post(
            "/api/v1/recommendations/generate",
            json={
                "student_id": str(test_student.id),
                "top_k": 5,
                "weights": {
                    "research_interest": 0.35,
                    "project_research": 0.25,
                    "publication_relevance": 0.25,
                    "skill_compatibility": 0.15,
                },
                "filters": {
                    "data_mode": "SYNTHETIC_ONLY",
                    "only_accepting_students": False,
                },
            },
        )
        assert rec_res.status_code == 200
        rec_data = rec_res.json()
        assert rec_data["total_candidates_evaluated"] > 0
        assert len(rec_data["recommendations"]) > 0
        assert rec_data["execution_time_ms"] > 0

        # 4. Inspect evidence, explanations, and scores
        top_rec = rec_data["recommendations"][0]
        assert top_rec["is_synthetic"] is True
        assert 0.0 <= top_rec["overall_score"] <= 1.0
        breakdown = top_rec["score_breakdown"]
        assert breakdown["research_interest_score"] >= 0.0
        assert breakdown["project_research_score"] >= 0.0
        assert breakdown["publication_relevance_score"] >= 0.0
        assert breakdown["skill_compatibility_score"] >= 0.0
        assert len(top_rec["explanation_summary"]) > 10

        # 5. Run offline IR benchmark evaluation
        bench_res = await client.post(
            "/api/v1/evaluation/benchmark?k_values=5,10",
            headers=admin_headers,
        )
        assert bench_res.status_code == 200
        bench_data = bench_res.json()
        assert "hybrid_embedding_scores" in bench_data
        assert "tfidf_baseline_scores" in bench_data
        hybrid = bench_data["hybrid_embedding_scores"]
        assert "ndcg@5" in hybrid
        assert "precision@5" in hybrid
        assert "recall@5" in hybrid
        assert "mrr" in hybrid


@pytest.mark.asyncio
class TestPhase7WorkflowB_RealData:
    """Workflow B: Real Research Data Ingestion, Provenance, and Recommendations."""

    async def test_workflow_b_real_data_cycle(
        self, client: AsyncClient, db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ):
        admin_headers = admin_auth_headers

        # 1. Ingest genuine OpenAlex works
        mock_works = [
            {
                "openalex_id": "https://openalex.org/W9988776655",
                "title": "Attention Is All You Need for Multimodal Learning",
                "doi": "10.1145/9988776655",
                "publication_year": 2024,
                "venue": "NeurIPS",
                "citation_count": 450,
                "abstract": "We introduce a novel transformer architecture for cross-modal alignment.",
                "authors": [{"openalex_id": "https://openalex.org/A111", "name": "Dr. Sarah Chen"}],
                "topics": ["Machine Learning", "Transformers"],
            }
        ]

        work_res = await client.post(
            "/api/v1/scholarly/import/works",
            json={"works": mock_works, "enrich_crossref": False, "auto_embed": True},
            headers=admin_headers,
        )
        assert work_res.status_code == 200
        w_data = work_res.json()
        assert w_data["created"] == 1
        assert w_data["status"] == "COMPLETED"

        # 2. Ingest genuine OpenAlex author (imported as PENDING_REVIEW)
        mock_authors = [
            {
                "openalex_id": "https://openalex.org/A111",
                "display_name": "Dr. Sarah Chen",
                "institution_name": "MIT CSAIL",
                "institution_ror": "https://ror.org/0420db125",
                "works_count": 45,
                "cited_by_count": 3200,
                "topics": ["Machine Learning", "Computer Vision"],
            }
        ]

        author_res = await client.post(
            "/api/v1/scholarly/import/authors",
            json={
                "authors": mock_authors,
                "default_department": "Computer Science",
                "default_status": "PENDING_REVIEW",
                "auto_embed": True,
            },
            headers=admin_headers,
        )
        assert author_res.status_code == 200
        a_data = author_res.json()
        assert a_data["created"] == 1

        # Verify faculty record attributes
        fac_stmt = select(Faculty).where(Faculty.openalex_id == "https://openalex.org/A111")
        sarah = (await db_session.execute(fac_stmt)).scalars().first()
        assert sarah is not None
        assert sarah.is_synthetic is False
        assert sarah.verification_status == "PENDING_REVIEW"
        assert sarah.institution_name == "MIT CSAIL"

        # 3. Ingest institutional CSV roster (automatically VERIFIED)
        csv_text = "first_name,last_name,email,department,title_rank,max_capacity\nRobert,Langdon,r.langdon@university.edu,Computer Science,FULL_PROFESSOR,6\n"
        csv_res = await client.post(
            "/api/v1/scholarly/import/csv",
            json={"csv_text": csv_text, "auto_embed": True},
            headers=admin_headers,
        )
        assert csv_res.status_code == 200
        c_data = csv_res.json()
        assert c_data["created"] == 1

        fac_stmt2 = select(Faculty).where(Faculty.last_name == "Langdon")
        robert = (await db_session.execute(fac_stmt2)).scalars().first()
        assert robert is not None
        assert robert.is_synthetic is False
        assert robert.verification_status == "VERIFIED"

        # 4. Verify deduplication: Re-importing same work must not create duplicate publication
        work_res_dup = await client.post(
            "/api/v1/scholarly/import/works",
            json={"works": mock_works, "enrich_crossref": False, "auto_embed": False},
            headers=admin_headers,
        )
        assert work_res_dup.status_code == 200
        w_dup_data = work_res_dup.json()
        assert w_dup_data["created"] == 0
        assert w_dup_data["updated"] == 1

        # 5. Verify provenance logging
        prov_stmt = select(EntityProvenance)
        provenance_records = (await db_session.execute(prov_stmt)).scalars().all()
        assert len(provenance_records) >= 2

        # 6. Create a test student to query recommendations
        test_user = User(
            id=uuid.uuid4(),
            email="alice.researcher@university.edu",
            hashed_password="hashed_pw_test",
            role="STUDENT",
            is_active=True,
        )
        db_session.add(test_user)
        await db_session.flush()

        test_student = Student(
            id=uuid.uuid4(),
            user_id=test_user.id,
            first_name="Alice",
            last_name="Researcher",
            department="Computer Science",
            degree_level="PHD",
            gpa_or_standing=3.95,
            statement_of_purpose="I research cross-modal attention mechanisms and multimodal transformers.",
            is_synthetic=False,
        )
        db_session.add(test_student)
        await db_session.commit()

        await client.post(
            "/api/v1/embeddings/sync", headers=admin_headers
        )

        # 7. Produce recommendations based on REAL_ONLY mode
        rec_res_real = await client.post(
            "/api/v1/recommendations/generate",
            json={
                "student_id": str(test_student.id),
                "top_k": 5,
                "filters": {
                    "data_mode": "REAL_ONLY",
                    "only_accepting_students": False,
                },
            },
        )
        assert rec_res_real.status_code == 200
        recs_real = rec_res_real.json()

        assert len(recs_real["recommendations"]) > 0
        for rec in recs_real["recommendations"]:
            assert rec["is_synthetic"] is False
            assert rec["verification_status"] in ["VERIFIED", "PENDING_REVIEW", "UNVERIFIED"]

        # 8. Test verified_only filter: Sarah Chen (PENDING_REVIEW) should be excluded
        rec_res_verified = await client.post(
            "/api/v1/recommendations/generate",
            json={
                "student_id": str(test_student.id),
                "top_k": 5,
                "filters": {
                    "data_mode": "REAL_ONLY",
                    "verified_only": True,
                },
            },
        )
        assert rec_res_verified.status_code == 200
        recs_verified = rec_res_verified.json()
        for rec in recs_verified["recommendations"]:
            assert rec["verification_status"] == "VERIFIED"
            assert rec["faculty_id"] != str(sarah.id)
