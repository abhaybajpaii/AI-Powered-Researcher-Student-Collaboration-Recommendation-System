"""Tests for the recommendation engine and API endpoints."""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.embeddings.service import embedding_service
from backend.app.models.project import AcademicProject
from backend.app.models.faculty import Faculty
from backend.app.models.publication import Publication, PublicationAuthorship
from backend.app.models.student import Student
from backend.app.models.embedding import EmbeddingRecord
from backend.app.models.taxonomy import (
    FacultySkillExpertise,
    StudentSkillInterest,
    StudentSkillInterest,
    TopicSkill,
)
from backend.app.models.user import User
from backend.app.recommendations.schemas import RecommendationRequest


@pytest_asyncio.fixture(scope="function")
async def recommendation_data(db_session: AsyncSession):
    """Creates a minimal dataset for testing recommendations:
    - 1 student with skills, SOP, and a project
    - 2 faculty with skills, bios, and publications
    - Shared taxonomy topics
    """
    # Taxonomy
    topic_ml = TopicSkill(
        id=uuid.uuid4(), name="Machine Learning", slug="machine-learning",
        category="RESEARCH_TOPIC",
    )
    topic_nlp = TopicSkill(
        id=uuid.uuid4(), name="Natural Language Processing", slug="nlp",
        category="RESEARCH_TOPIC",
    )
    topic_cv = TopicSkill(
        id=uuid.uuid4(), name="Computer Vision", slug="computer-vision",
        category="RESEARCH_TOPIC",
    )
    db_session.add_all([topic_ml, topic_nlp, topic_cv])
    await db_session.flush()

    # Student
    stu_user = User(
        id=uuid.uuid4(), email="rec_student@test.edu",
        hashed_password="test", role="STUDENT", is_active=True,
    )
    db_session.add(stu_user)
    await db_session.flush()

    student = Student(
        id=uuid.uuid4(), user_id=stu_user.id,
        first_name="Alice", last_name="Chen",
        department="Computer Science", degree_level="PHD",
        statement_of_purpose="I am passionate about NLP and want to build better language models using transformer architectures.",
    )
    db_session.add(student)
    await db_session.flush()

    # Student skills
    stu_skill1 = StudentSkillInterest(
        id=uuid.uuid4(), student_id=student.id, topic_skill_id=topic_ml.id,
        proficiency_level=4, interest_level=5,
    )
    stu_skill2 = StudentSkillInterest(
        id=uuid.uuid4(), student_id=student.id, topic_skill_id=topic_nlp.id,
        proficiency_level=4, interest_level=5,
    )
    db_session.add_all([stu_skill1, stu_skill2])

    # Faculty 1 - NLP expert (should rank higher)
    fac_user1 = User(
        id=uuid.uuid4(), email="rec_prof1@test.edu",
        hashed_password="test", role="FACULTY", is_active=True,
    )
    db_session.add(fac_user1)
    await db_session.flush()

    faculty1 = Faculty(
        id=uuid.uuid4(), user_id=fac_user1.id,
        first_name="Dr. Bob", last_name="Williams",
        department="Computer Science", title_rank="ASSOCIATE_PROFESSOR",
        bio="Expert in NLP, large language models, and text understanding.",
        lab_name="Language Intelligence Lab",
        accepting_students=True, max_capacity=5, current_student_count=1,
    )
    db_session.add(faculty1)
    await db_session.flush()

    fac1_skill = FacultySkillExpertise(
        id=uuid.uuid4(), faculty_id=faculty1.id, topic_skill_id=topic_nlp.id,
        expertise_level=5, is_primary_focus=True,
    )
    fac1_skill2 = FacultySkillExpertise(
        id=uuid.uuid4(), faculty_id=faculty1.id, topic_skill_id=topic_ml.id,
        expertise_level=4, is_primary_focus=False,
    )
    db_session.add_all([fac1_skill, fac1_skill2])

    pub1 = Publication(
        id=uuid.uuid4(), title="Transformer Models for Language Understanding",
        abstract="We present novel transformer architectures for NLP tasks.",
        venue="ACL", publication_year=2024,
        title_hash="test_hash_" + uuid.uuid4().hex[:8],
    )
    db_session.add(pub1)
    await db_session.flush()

    auth1 = PublicationAuthorship(
        id=uuid.uuid4(), publication_id=pub1.id, faculty_id=faculty1.id,
        author_order=1, raw_author_name="Dr. Bob Williams", is_corresponding=True,
    )
    db_session.add(auth1)

    # Faculty 2 - CV expert (should rank lower for NLP student)
    fac_user2 = User(
        id=uuid.uuid4(), email="rec_prof2@test.edu",
        hashed_password="test", role="FACULTY", is_active=True,
    )
    db_session.add(fac_user2)
    await db_session.flush()

    faculty2 = Faculty(
        id=uuid.uuid4(), user_id=fac_user2.id,
        first_name="Dr. Carol", last_name="Davis",
        department="Electrical Engineering", title_rank="FULL_PROFESSOR",
        bio="Expert in computer vision and image segmentation.",
        lab_name="Vision Systems Lab",
        accepting_students=True, max_capacity=3, current_student_count=2,
    )
    db_session.add(faculty2)
    await db_session.flush()

    fac2_skill = FacultySkillExpertise(
        id=uuid.uuid4(), faculty_id=faculty2.id, topic_skill_id=topic_cv.id,
        expertise_level=5, is_primary_focus=True,
    )
    db_session.add(fac2_skill)

    pub2 = Publication(
        id=uuid.uuid4(), title="Real-Time Object Detection in Autonomous Vehicles",
        abstract="We develop high-speed object detection algorithms for self-driving cars.",
        venue="CVPR", publication_year=2024,
        title_hash="test_hash_" + uuid.uuid4().hex[:8],
    )
    db_session.add(pub2)
    await db_session.flush()

    auth2 = PublicationAuthorship(
        id=uuid.uuid4(), publication_id=pub2.id, faculty_id=faculty2.id,
        author_order=1, raw_author_name="Dr. Carol Davis", is_corresponding=True,
    )
    db_session.add(auth2)

    await db_session.commit()

    return {
        "student": student,
        "faculty1": faculty1,
        "faculty2": faculty2,
        "topics": {"ml": topic_ml, "nlp": topic_nlp, "cv": topic_cv},
    }


class TestRecommendationAPI:
    """Integration tests for the recommendation endpoints."""

    @pytest.mark.asyncio
    async def test_generate_recommendations_endpoint(self, client, recommendation_data):
        data = recommendation_data
        response = await client.post(
            "/api/v1/recommendations/generate",
            json={
                "student_id": str(data["student"].id),
                "top_k": 5,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "run_id" in body
        assert body["student_id"] == str(data["student"].id)
        assert body["total_candidates_evaluated"] >= 2
        assert len(body["recommendations"]) >= 1

        # Verify each recommendation has required fields
        for rec in body["recommendations"]:
            assert "faculty_id" in rec
            assert "faculty_name" in rec
            assert "overall_score" in rec
            assert "score_breakdown" in rec
            assert "explanation_summary" in rec
            assert rec["overall_score"] >= 0.0

    @pytest.mark.asyncio
    async def test_repeated_recommendation_runs_reuse_project_embeddings(
        self, client, db_session: AsyncSession, recommendation_data
    ):
        student = recommendation_data["student"]
        payload = {"student_id": str(student.id), "top_k": 5}

        first_response = await client.post(
            "/api/v1/recommendations/generate", json=payload
        )
        assert first_response.status_code == 200
        embeddings_after_first = (
            await db_session.execute(select(EmbeddingRecord))
        ).scalars().all()

        second_response = await client.post(
            "/api/v1/recommendations/generate", json=payload
        )
        assert second_response.status_code == 200
        assert second_response.json()["run_id"] != first_response.json()["run_id"]

        embeddings_after_second = (
            await db_session.execute(select(EmbeddingRecord))
        ).scalars().all()
        assert len(embeddings_after_second) == len(embeddings_after_first)

    @pytest.mark.asyncio
    async def test_nlp_faculty_ranks_higher_for_nlp_student(self, client, recommendation_data):
        """The NLP-expert faculty should score higher than the CV-expert for an NLP-focused student."""
        data = recommendation_data
        response = await client.post(
            "/api/v1/recommendations/generate",
            json={
                "student_id": str(data["student"].id),
                "top_k": 10,
            },
        )
        assert response.status_code == 200
        recs = response.json()["recommendations"]

        # Find scores for both faculty
        fac1_score = None
        fac2_score = None
        for rec in recs:
            if rec["faculty_id"] == str(data["faculty1"].id):
                fac1_score = rec["overall_score"]
            elif rec["faculty_id"] == str(data["faculty2"].id):
                fac2_score = rec["overall_score"]

        assert fac1_score is not None, "NLP faculty should appear in recommendations"
        assert fac2_score is not None, "CV faculty should appear in recommendations"
        assert fac1_score >= fac2_score, (
            f"NLP-expert ({fac1_score}) should score >= CV-expert ({fac2_score}) for NLP student"
        )

    @pytest.mark.asyncio
    async def test_get_recommendation_run(self, client, recommendation_data):
        """Should be able to retrieve a past recommendation run."""
        data = recommendation_data
        gen_response = await client.post(
            "/api/v1/recommendations/generate",
            json={"student_id": str(data["student"].id), "top_k": 5},
        )
        run_id = gen_response.json()["run_id"]

        detail_response = await client.get(f"/api/v1/recommendations/runs/{run_id}")
        assert detail_response.status_code == 200
        body = detail_response.json()
        assert body["run_id"] == run_id
        assert len(body["results"]) >= 1

    @pytest.mark.asyncio
    async def test_get_recommendation_history(self, client, recommendation_data):
        data = recommendation_data
        # Generate two runs
        await client.post(
            "/api/v1/recommendations/generate",
            json={"student_id": str(data["student"].id), "top_k": 3},
        )
        await client.post(
            "/api/v1/recommendations/generate",
            json={"student_id": str(data["student"].id), "top_k": 5},
        )

        history_response = await client.get(
            f"/api/v1/recommendations/history/{data['student'].id}"
        )
        assert history_response.status_code == 200
        body = history_response.json()
        assert body["total_runs"] >= 2

    @pytest.mark.asyncio
    async def test_invalid_student_returns_404(self, client, recommendation_data):
        response = await client.post(
            "/api/v1/recommendations/generate",
            json={"student_id": str(uuid.uuid4()), "top_k": 5},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_score_breakdown_present(self, client, recommendation_data):
        data = recommendation_data
        response = await client.post(
            "/api/v1/recommendations/generate",
            json={"student_id": str(data["student"].id), "top_k": 5},
        )
        recs = response.json()["recommendations"]
        for rec in recs:
            bd = rec["score_breakdown"]
            assert "research_interest_score" in bd
            assert "project_research_score" in bd
            assert "publication_relevance_score" in bd
            assert "skill_compatibility_score" in bd
            assert "normalized_weights" in bd

    @pytest.mark.asyncio
    async def test_missing_projects_and_skills_are_removed_from_active_weights(
        self, client, recommendation_data, db_session: AsyncSession
    ):
        student = recommendation_data["student"]
        await db_session.execute(
            delete(AcademicProject).where(AcademicProject.student_id == student.id)
        )
        await db_session.execute(
            delete(StudentSkillInterest).where(
                StudentSkillInterest.student_id == student.id
            )
        )
        await db_session.flush()

        response = await client.post(
            "/api/v1/recommendations/generate",
            json={"student_id": str(student.id), "top_k": 5},
        )

        assert response.status_code == 200
        recommendation = response.json()["recommendations"][0]
        weights = recommendation["score_breakdown"]["normalized_weights"]
        assert "project_research" not in weights
        assert "skill_compatibility" not in weights
        assert sum(weights.values()) == pytest.approx(1.0)
        assert any("past projects" in caveat for caveat in recommendation["missing_data_caveats"])

    @pytest.mark.asyncio
    async def test_synced_embeddings_use_bulk_lookup(
        self, client, recommendation_data, db_session: AsyncSession, monkeypatch
    ):
        await embedding_service.sync_all_embeddings(db_session)

        async def fail_if_embedding_lookup_is_not_batched(*_args, **_kwargs):
            raise AssertionError("Existing embeddings should come from the bulk query")

        monkeypatch.setattr(
            embedding_service,
            "get_or_create_embedding",
            fail_if_embedding_lookup_is_not_batched,
        )

        response = await client.post(
            "/api/v1/recommendations/generate",
            json={"student_id": str(recommendation_data["student"].id), "top_k": 5},
        )

        assert response.status_code == 200
        assert response.json()["recommendations"]
