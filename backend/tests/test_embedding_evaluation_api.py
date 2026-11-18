"""Tests for the embedding and evaluation API endpoints."""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.evaluation import RelevanceJudgment
from backend.app.models.faculty import Faculty
from backend.app.models.publication import Publication, PublicationAuthorship
from backend.app.models.student import Student
from backend.app.models.taxonomy import (
    FacultySkillExpertise,
    StudentSkillInterest,
    TopicSkill,
)
from backend.app.models.user import User


@pytest_asyncio.fixture(scope="function")
async def embedding_api_data(db_session: AsyncSession):
    """Creates minimal entities for testing the embedding endpoints."""
    user = User(
        id=uuid.uuid4(), email="embed_api_student@test.edu",
        hashed_password="test", role="STUDENT", is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    student = Student(
        id=uuid.uuid4(), user_id=user.id,
        first_name="Test", last_name="Student",
        department="CS", degree_level="MASTERS",
        statement_of_purpose="Research in deep learning.",
    )
    db_session.add(student)

    fac_user = User(
        id=uuid.uuid4(), email="embed_api_prof@test.edu",
        hashed_password="test", role="FACULTY", is_active=True,
    )
    db_session.add(fac_user)
    await db_session.flush()

    faculty = Faculty(
        id=uuid.uuid4(), user_id=fac_user.id,
        first_name="Dr", last_name="Test",
        department="CS", title_rank="ASSISTANT_PROFESSOR",
        bio="Specializes in deep learning.", lab_name="DL Lab",
        accepting_students=True, max_capacity=5, current_student_count=0,
    )
    db_session.add(faculty)

    pub = Publication(
        id=uuid.uuid4(), title="DL for NLP",
        abstract="We use deep learning for natural language processing.",
        venue="EMNLP", publication_year=2024,
        title_hash="api_test_hash_" + uuid.uuid4().hex[:8],
    )
    db_session.add(pub)
    await db_session.flush()

    auth = PublicationAuthorship(
        id=uuid.uuid4(), publication_id=pub.id, faculty_id=faculty.id,
        author_order=1, raw_author_name="Dr Test", is_corresponding=True,
    )
    db_session.add(auth)
    await db_session.commit()

    return {"student": student, "faculty": faculty, "publication": pub}


class TestEmbeddingAPI:
    @pytest.mark.asyncio
    async def test_sync_embeddings(
        self, client, embedding_api_data, admin_auth_headers
    ):
        response = await client.post(
            "/api/v1/embeddings/sync", headers=admin_auth_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "sync_complete"
        assert "model_name" in body
        assert body["students_embedded"] >= 1
        assert body["faculty_embedded"] >= 1
        assert body["publications_embedded"] >= 1

    @pytest.mark.asyncio
    async def test_embedding_stats(
        self, client, embedding_api_data, admin_auth_headers
    ):
        # First sync
        await client.post("/api/v1/embeddings/sync", headers=admin_auth_headers)
        # Then get stats
        response = await client.get(
            "/api/v1/embeddings/stats", headers=admin_auth_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total_embeddings"] >= 1
        assert "by_entity_type" in body
        assert "by_model" in body

    @pytest.mark.asyncio
    async def test_get_entity_embedding(
        self, client, embedding_api_data, admin_auth_headers
    ):
        data = embedding_api_data
        # Sync first
        await client.post("/api/v1/embeddings/sync", headers=admin_auth_headers)
        # Then lookup
        response = await client.get(
            f"/api/v1/embeddings/entity/STUDENT/{data['student'].id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["entity_type"] == "STUDENT"
        assert len(body["embeddings"]) >= 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_embedding_404(
        self, client, embedding_api_data, admin_auth_headers
    ):
        response = await client.get(
            f"/api/v1/embeddings/entity/STUDENT/{uuid.uuid4()}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404


class TestEvaluationAPI:
    @pytest.mark.asyncio
    async def test_benchmark_no_judgments(
        self, client, embedding_api_data, admin_auth_headers
    ):
        """When no relevance judgments exist, should return a clear status."""
        response = await client.post(
            "/api/v1/evaluation/benchmark?benchmark_suite=nonexistent_suite",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "NO_JUDGMENTS_FOUND"

    @pytest.mark.asyncio
    async def test_benchmark_with_judgments(
        self, client, db_session, embedding_api_data, admin_auth_headers
    ):
        """With relevance judgments, should produce comparison metrics."""
        data = embedding_api_data

        # Insert a relevance judgment
        judgment = RelevanceJudgment(
            id=uuid.uuid4(),
            student_id=data["student"].id,
            faculty_id=data["faculty"].id,
            benchmark_suite="test_suite_v1",
            relevance_grade=3,  # Highly relevant
            annotator_id="test_annotator",
        )
        db_session.add(judgment)
        await db_session.commit()

        response = await client.post(
            "/api/v1/evaluation/benchmark?benchmark_suite=test_suite_v1&k_values=5",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        # Should either have comparison metrics or a valid status
        assert "benchmark_suite" in body
        assert body["benchmark_suite"] == "test_suite_v1"
