"""Unit and Integration Tests for Phase 6 Real Research Data Integration.

Covers:
- OpenAlex client & inverted index reconstruction
- Crossref client & conflict resolution strategy
- Institutional CSV importer validation
- Ingestion of real works & authors with provenance and vector embeddings
- Verification status transitions
- Recommendation engine filtering by operating mode (REAL_ONLY, SYNTHETIC_ONLY, ALL)
- Manual ground-truth relevance judgment curation for honest evaluation
"""

import uuid
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.connectors.crossref_client import crossref_client, strip_jats_tags
from backend.app.connectors.csv_importer import csv_importer
from backend.app.connectors.openalex_client import (
    OpenAlexClient,
    reconstruct_abstract_from_inverted_index,
)
from backend.app.models.faculty import Faculty
from backend.app.models.provenance import EntityProvenance, ImportJob
from backend.app.models.publication import Publication
from backend.app.models.student import Student
from backend.app.models.user import User


class TestAbstractReconstruction:
    """Tests reconstruction of text from OpenAlex's abstract_inverted_index."""

    def test_reconstruct_basic_inverted_index(self):
        index = {
            "Deep": [0],
            "learning": [1],
            "models": [2],
            "exhibit": [3],
            "remarkable": [4],
            "performance": [5],
            "on": [6],
            "reasoning": [7],
            "benchmarks.": [8],
        }
        text = reconstruct_abstract_from_inverted_index(index)
        assert text == "Deep learning models exhibit remarkable performance on reasoning benchmarks."

    def test_reconstruct_repeated_words(self):
        index = {
            "The": [0, 4],
            "model": [1, 5],
            "outperforms": [2],
            "all": [3],
            "baselines.": [6],
        }
        text = reconstruct_abstract_from_inverted_index(index)
        assert text == "The model outperforms all The model baselines."

    def test_reconstruct_empty_or_none(self):
        assert reconstruct_abstract_from_inverted_index(None) == ""
        assert reconstruct_abstract_from_inverted_index({}) == ""


class TestCrossrefEnrichment:
    """Tests Crossref parser, JATS tag cleaning, and conflict resolution."""

    def test_strip_jats_xml_tags(self):
        raw = "<jats:p>Recent advances in <jats:italic>graph neural networks</jats:italic> enable scalable analysis.</jats:p>"
        clean = strip_jats_tags(raw)
        assert clean == "Recent advances in graph neural networks enable scalable analysis."

    def test_conflict_resolution_rules(self):
        openalex = {
            "title": "Quantum Computation and Information",
            "abstract": "No abstract provided in OpenAlex record.",
            "venue": None,
            "publication_year": None,
            "doi": "10.1017/CBO9780511976667",
        }
        crossref = {
            "title": "Quantum Computation",
            "abstract": "Comprehensive textbook covering quantum information theory.",
            "venue": "Cambridge University Press",
            "publication_year": 2010,
        }

        resolved = crossref_client.resolve_conflicts(openalex, crossref)
        assert resolved["abstract"] == "Comprehensive textbook covering quantum information theory."
        assert resolved["venue"] == "Cambridge University Press"
        assert resolved["publication_year"] == 2010
        assert resolved["crossref_enriched"] is True
        assert len(resolved["resolution_notes"]) >= 2


class TestInstitutionalCsvImporter:
    """Tests parsing and validation of official institutional faculty CSV rosters."""

    def test_parse_valid_csv(self):
        csv_data = """first_name,last_name,email,department,title_rank,max_capacity
Alice,Vanderbilt,a.vanderbilt@university.edu,Computer Science,FULL_PROFESSOR,8
Bob,Sterling,b.sterling@university.edu,Electrical Engineering,ASSOCIATE_PROFESSOR,4
"""
        dtos, errors = csv_importer.parse_faculty_csv(csv_data)
        assert len(errors) == 0
        assert len(dtos) == 2
        assert dtos[0].first_name == "Alice"
        assert dtos[0].department == "Computer Science"
        assert dtos[0].verification_status == "VERIFIED"
        assert dtos[0].is_synthetic is False
        assert dtos[0].max_capacity == 8

    def test_missing_required_headers(self):
        bad_csv = """first_name,last_name,phone
Alice,Vanderbilt,555-1234
"""
        dtos, errors = csv_importer.parse_faculty_csv(bad_csv)
        assert len(dtos) == 0
        assert len(errors) == 1
        assert "Missing required CSV column headers" in errors[0]["error"]


@pytest.mark.asyncio
class TestRealDataIngestionAndModeFiltering:
    """Integration tests for real scholarly data ingestion and recommendation mode separation."""

    async def test_scholarly_search_endpoints_require_admin(self, client: AsyncClient):
        # Without admin privileges -> 401 or 403
        res = await client.get("/api/v1/scholarly/search/works?query=transformer")
        assert res.status_code in (401, 403)

    async def test_import_openalex_works_and_authors(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ):
        admin_headers = admin_auth_headers

        mock_work = {
            "id": "https://openalex.org/W2741809807",
            "openalex_id": "https://openalex.org/W2741809807",
            "title": "Attention Is All You Need",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
            "publication_year": 2017,
            "venue": "Advances in Neural Information Processing Systems",
            "doi": "10.48550/arXiv.1706.03762",
            "citation_count": 95000,
            "authors": [
                {"name": "Ashish Vaswani", "openalex_id": "https://openalex.org/A5023880860"},
                {"name": "Noam Shazeer", "openalex_id": "https://openalex.org/A5012345678"},
            ],
        }

        # 1. Import work
        work_res = await client.post(
            "/api/v1/scholarly/import/works",
            json={"works": [mock_work], "enrich_crossref": False, "auto_embed": True},
            headers=admin_headers,
        )
        assert work_res.status_code == 200
        w_data = work_res.json()
        assert w_data["created"] == 1
        assert w_data["status"] == "COMPLETED"

        # Verify publication in database
        stmt = select(Publication).where(Publication.openalex_id == "https://openalex.org/W2741809807")
        pub = (await db_session.execute(stmt)).scalars().first()
        assert pub is not None
        assert pub.is_synthetic is False
        assert pub.citation_count == 95000

        # Verify provenance was logged
        prov_stmt = select(EntityProvenance).where(
            EntityProvenance.entity_type == "PUBLICATION",
            EntityProvenance.entity_id == pub.id,
        )
        prov = (await db_session.execute(prov_stmt)).scalars().first()
        assert prov is not None
        assert prov.external_id == "https://openalex.org/W2741809807"

        # 2. Import Author as Pending Faculty
        mock_author = {
            "id": "https://openalex.org/A5023880860",
            "openalex_id": "https://openalex.org/A5023880860",
            "display_name": "Ashish Vaswani",
            "institution_name": "University AI Lab",
            "institution_ror": "https://ror.org/03vek6s52",
            "works_count": 45,
            "cited_by_count": 105000,
            "topics": ["Natural Language Processing", "Attention Mechanisms", "Deep Learning"],
        }

        author_res = await client.post(
            "/api/v1/scholarly/import/authors",
            json={
                "authors": [mock_author],
                "default_department": "Computer Science",
                "default_status": "PENDING_REVIEW",
                "auto_embed": True,
            },
            headers=admin_headers,
        )
        assert author_res.status_code == 200
        a_data = author_res.json()
        assert a_data["created"] == 1

        # Verify faculty record
        fac_stmt = select(Faculty).where(Faculty.openalex_id == "https://openalex.org/A5023880860")
        fac = (await db_session.execute(fac_stmt)).scalars().first()
        assert fac is not None
        assert fac.is_synthetic is False
        assert fac.verification_status == "PENDING_REVIEW"
        assert fac.department == "Computer Science"

        # 3. Test Faculty Verification Workflow: Update status to VERIFIED
        verify_res = await client.put(
            f"/api/v1/scholarly/verification/faculty/{fac.id}",
            json={
                "verification_status": "VERIFIED",
                "verification_notes": "Verified faculty member through university appointment letter.",
                "department": "Computer Science & Engineering",
                "title_rank": "ASSOCIATE_PROFESSOR",
            },
            headers=admin_headers,
        )
        assert verify_res.status_code == 200
        v_data = verify_res.json()
        assert v_data["verification_status"] == "VERIFIED"
        assert v_data["verified_at"] is not None

        # Verify persistence in DB
        await db_session.refresh(fac)
        assert fac.verification_status == "VERIFIED"
        assert fac.department == "Computer Science & Engineering"
        assert fac.verified_at is not None

        # 4. Check Data Summary API
        summary_res = await client.get(
            "/api/v1/scholarly/summary", headers=admin_headers
        )
        assert summary_res.status_code == 200
        s_data = summary_res.json()
        assert s_data["faculty"]["real_count"] >= 1
        assert s_data["publications"]["real_count"] >= 1

    async def test_recommendation_operating_mode_filtering(
        self, client: AsyncClient, db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ):
        admin_headers = admin_auth_headers

        # 1. Seed synthetic baseline
        await client.post("/api/v1/admin/seed-synthetic", headers=admin_headers)

        # 2. Add a real verified faculty member
        user = User(
            id=uuid.uuid4(),
            email=f"real.faculty.{uuid.uuid4().hex[:4]}@university.edu",
            hashed_password="hashed_pw_test",
            role="FACULTY",
        )
        db_session.add(user)
        await db_session.flush()

        real_fac = Faculty(
            id=uuid.uuid4(),
            user_id=user.id,
            first_name="Geoffrey",
            last_name="Hinton",
            department="Computer Science",
            title_rank="FULL_PROFESSOR",
            bio="Pioneer in deep neural networks and representation learning.",
            is_synthetic=False,
            verification_status="VERIFIED",
            openalex_id="https://openalex.org/A5023880999",
            accepting_students=True,
            max_capacity=5,
        )
        db_session.add(real_fac)
        await db_session.commit()

        # Fetch an existing student
        stu = (await db_session.execute(select(Student))).scalars().first()
        assert stu is not None

        # Mode: REAL_ONLY
        real_rec = await client.post(
            "/api/v1/recommendations/generate",
            json={
                "student_id": str(stu.id),
                "top_k": 5,
                "filters": {
                    "data_mode": "REAL_ONLY",
                    "verified_only": True,
                },
            },
        )
        assert real_rec.status_code == 200
        real_items = real_rec.json()["recommendations"]
        assert len(real_items) >= 1
        for item in real_items:
            assert item["is_synthetic"] is False
            assert item["verification_status"] == "VERIFIED"

        # Mode: SYNTHETIC_ONLY
        synth_rec = await client.post(
            "/api/v1/recommendations/generate",
            json={
                "student_id": str(stu.id),
                "top_k": 5,
                "filters": {
                    "data_mode": "SYNTHETIC_ONLY",
                },
            },
        )
        assert synth_rec.status_code == 200
        synth_items = synth_rec.json()["recommendations"]
        assert len(synth_items) >= 1
        for item in synth_items:
            assert item["is_synthetic"] is True

    async def test_manual_relevance_judgment_creation(
        self, client: AsyncClient, db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ):
        admin_headers = admin_auth_headers
        await client.post("/api/v1/admin/seed-synthetic", headers=admin_headers)

        stu = (await db_session.execute(select(Student))).scalars().first()
        fac = (await db_session.execute(select(Faculty))).scalars().first()
        assert stu is not None
        assert fac is not None

        res = await client.post(
            "/api/v1/evaluation/judgments",
            json={
                "student_id": str(stu.id),
                "faculty_id": str(fac.id),
                "relevance_grade": 3,
                "benchmark_suite": "real_data_eval_v1",
                "notes": "Expert curator identified shared focus on self-attention architectures.",
                "annotator_id": "curator_expert_1",
            },
            headers=admin_headers,
        )
        assert res.status_code == 200
        j_data = res.json()
        assert j_data["relevance_grade"] == 3
        assert j_data["benchmark_suite"] == "real_data_eval_v1"
