"""Comprehensive Full-System Integration Test.

Verifies end-to-end integration across all system components:
1. Student registration and authentication.
2. Student profile creation and updates.
3. Student skills and project management.
4. Faculty profile and publication retrieval.
5. Embedding generation and synchronization.
6. Recommendation generation.
7. Recommendation ranking and explanations.
8. Recommendation feedback submission & persistence.
9. Benchmark evaluation.
10. Database relationships & foreign-key cascade consistency.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.security import get_password_hash
from backend.app.models.faculty import Faculty
from backend.app.models.project import AcademicProject
from backend.app.models.publication import Publication, PublicationAuthorship
from backend.app.models.recommendation import RecommendationResult, RecommendationRun
from backend.app.models.student import Student
from backend.app.models.taxonomy import FacultySkillExpertise, StudentSkillInterest, TopicSkill
from backend.app.models.user import User


@pytest.mark.asyncio
class TestFullSystemIntegrationWorkflow:
    """Verifies complete data flow and integration across all system components."""

    async def test_end_to_end_system_lifecycle(
        self, client: AsyncClient, db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ):
        admin_headers = admin_auth_headers

        # -----------------------------------------------------------------
        # 1. Student Registration & Authentication
        # -----------------------------------------------------------------
        stu_email = f"integration_stu_{uuid.uuid4().hex[:6]}@university.edu"
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": stu_email,
                "password": "Password123!",
                "role": "STUDENT",
                "first_name": "Clara",
                "last_name": "Oswald",
                "department": "Computer Science",
                "statement_of_purpose": "Research on deep representation learning and multilingual transformers.",
                "bio": "Graduate researcher.",
            },
        )
        assert reg_res.status_code == 201
        auth_data = reg_res.json()
        token = auth_data["access_token"]
        student_id = auth_data["user"]["student_id"]
        stu_headers = {"Authorization": f"Bearer {token}"}

        # Verify /auth/me returns registered student
        me_res = await client.get("/api/v1/auth/me", headers=stu_headers)
        assert me_res.status_code == 200
        assert me_res.json()["student_id"] == student_id
        assert me_res.json()["email"] == stu_email

        # -----------------------------------------------------------------
        # 2. Student Profile Creation & Updates
        # -----------------------------------------------------------------
        upd_res = await client.put(
            f"/api/v1/students/{student_id}",
            json={
                "gpa_or_standing": 3.92,
                "graduation_year": 2026,
                "degree_level": "MASTERS",
                "availability_status": "SEEKING_ADVISOR",
            },
            headers=stu_headers,
        )
        assert upd_res.status_code == 200
        assert upd_res.json()["gpa_or_standing"] == 3.92

        # -----------------------------------------------------------------
        # 3. Student Skills and Project Management
        # -----------------------------------------------------------------
        # Create a topic directly in DB for clean association
        topic = TopicSkill(
            id=uuid.uuid4(),
            name="Natural Language Processing",
            slug="nlp-transformers",
            category="RESEARCH_TOPIC",
            description="NLP and Transformer architectures",
        )
        db_session.add(topic)
        await db_session.commit()

        # Add skill to student
        skill_res = await client.post(
            f"/api/v1/students/{student_id}/skills",
            json={
                "topic_skill_id": str(topic.id),
                "proficiency_level": 5,
                "interest_level": 5,
                "years_experience": 2.5,
            },
            headers=stu_headers,
        )
        assert skill_res.status_code == 201
        skill_id = skill_res.json()["id"]

        # Add academic project
        proj_res = await client.post(
            f"/api/v1/students/{student_id}/projects",
            json={
                "title": "Cross-Lingual Language Modeling",
                "description": "Pretrained masked language models across diverse language families.",
                "role": "Principal Student Investigator",
                "github_url": "https://github.com/clara/cl-lm",
            },
            headers=stu_headers,
        )
        assert proj_res.status_code == 201
        project_id = proj_res.json()["id"]

        # Verify student details include both skill and project
        stu_detail = (await client.get(f"/api/v1/students/{student_id}")).json()
        assert len(stu_detail["skills_interests"]) == 1
        assert len(stu_detail["academic_projects"]) == 1
        assert stu_detail["skills_interests"][0]["id"] == skill_id
        assert stu_detail["academic_projects"][0]["id"] == project_id

        # -----------------------------------------------------------------
        # 4. Faculty Profile & Publication Management
        # -----------------------------------------------------------------
        fac_email = f"prof_oswald_{uuid.uuid4().hex[:6]}@university.edu"
        fac_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": fac_email,
                "password": "Password123!",
                "role": "FACULTY",
                "first_name": "Prof. Alistair",
                "last_name": "Lethbridge",
                "department": "Computer Science",
                "bio": "Investigating self-supervised foundation models and NLP reasoning.",
            },
        )
        assert fac_reg.status_code == 400
        assert fac_reg.json()["detail"] == "Public registration is limited to STUDENT accounts."

        # Provision this test-only faculty profile through the trusted test setup,
        # then exercise the normal login and faculty APIs.
        faculty_user = User(
            id=uuid.uuid4(),
            email=fac_email,
            hashed_password=get_password_hash("Password123!"),
            role="FACULTY",
            is_active=True,
        )
        db_session.add(faculty_user)
        await db_session.flush()
        faculty = Faculty(
            id=uuid.uuid4(),
            user_id=faculty_user.id,
            first_name="Prof. Alistair",
            last_name="Lethbridge",
            department="Computer Science",
            bio="Investigating self-supervised foundation models and NLP reasoning.",
        )
        db_session.add(faculty)
        await db_session.commit()
        faculty_id = str(faculty.id)
        fac_login = await client.post(
            "/api/v1/auth/login",
            json={"email": fac_email, "password": "Password123!"},
        )
        assert fac_login.status_code == 200
        fac_token = fac_login.json()["access_token"]
        fac_headers = {"Authorization": f"Bearer {fac_token}"}

        # Update faculty profile
        fac_upd = await client.put(
            f"/api/v1/faculty/{faculty_id}",
            json={
                "lab_name": "Language and Intelligence Lab",
                "title_rank": "ASSOCIATE_PROFESSOR",
                "max_capacity": 5,
                "accepting_students": True,
            },
            headers=fac_headers,
        )
        assert fac_upd.status_code == 200

        # Attach faculty expertise skill and publication
        fac_skill = FacultySkillExpertise(
            id=uuid.uuid4(),
            faculty_id=uuid.UUID(faculty_id),
            topic_skill_id=topic.id,
            expertise_level=5,
            is_primary_focus=True,
        )
        db_session.add(fac_skill)

        pub = Publication(
            id=uuid.uuid4(),
            title="Multilingual Reasoning in Foundation Language Models",
            abstract="We present an empirical study on cross-lingual transfer in transformer models.",
            venue="ACL 2025",
            publication_year=2025,
            title_hash=uuid.uuid4().hex,
            is_synthetic=False,
        )
        db_session.add(pub)
        await db_session.flush()

        auth = PublicationAuthorship(
            id=uuid.uuid4(),
            publication_id=pub.id,
            faculty_id=uuid.UUID(faculty_id),
            author_order=1,
            raw_author_name="Prof. Alistair Lethbridge",
            is_corresponding=True,
        )
        db_session.add(auth)
        await db_session.commit()

        # Retrieve faculty profile via API
        fac_get = (await client.get(f"/api/v1/faculty/{faculty_id}")).json()
        assert fac_get["id"] == faculty_id
        assert len(fac_get["skills_expertise"]) == 1

        # -----------------------------------------------------------------
        # 5. Embedding Generation & Synchronization
        # -----------------------------------------------------------------
        sync_res = await client.post(
            "/api/v1/embeddings/sync", headers=admin_headers
        )
        assert sync_res.status_code == 200
        sync_info = sync_res.json()
        assert sync_info["status"] == "sync_complete"
        assert sync_info["dimension"] == 384

        stats_res = (
            await client.get(
                "/api/v1/embeddings/stats", headers=admin_headers
            )
        ).json()
        assert stats_res["total_embeddings"] >= 4
        assert stats_res["active_dimension"] == 384

        # -----------------------------------------------------------------
        # 6 & 7. Recommendation Generation, Ranking & Explanations
        # -----------------------------------------------------------------
        rec_res = await client.post(
            "/api/v1/recommendations/generate",
            json={
                "student_id": student_id,
                "top_k": 5,
                "weights": {
                    "research_interest": 0.35,
                    "project_research": 0.25,
                    "publication_relevance": 0.25,
                    "skill_compatibility": 0.15,
                },
                "filters": {
                    "only_accepting_students": True,
                },
            },
            headers=stu_headers,
        )
        assert rec_res.status_code == 200
        rec_data = rec_res.json()
        run_id = rec_data["run_id"]
        assert len(rec_data["recommendations"]) >= 1

        top_match = rec_data["recommendations"][0]
        assert top_match["rank_position"] == 1
        assert 0.0 <= top_match["overall_score"] <= 1.0
        assert len(top_match["explanation_summary"]) > 10

        # Verify score breakdown
        breakdown = top_match["score_breakdown"]
        assert breakdown["research_interest_score"] >= 0.0
        assert breakdown["project_research_score"] >= 0.0
        assert breakdown["publication_relevance_score"] >= 0.0
        assert breakdown["skill_compatibility_score"] >= 0.0

        # -----------------------------------------------------------------
        # 8. Recommendation Feedback Submission & History Tracking
        # -----------------------------------------------------------------
        fb_res = await client.post(
            f"/api/v1/recommendations/runs/{run_id}/results/{top_match['faculty_id']}/feedback",
            params={"rating": 5, "notes": "Exceptional research match for transformers."},
            headers=stu_headers,
        )
        assert fb_res.status_code == 200

        # Verify feedback in run details
        run_detail = (await client.get(f"/api/v1/recommendations/runs/{run_id}")).json()
        matched_result = next(r for r in run_detail["results"] if r["faculty_id"] == top_match["faculty_id"])
        assert matched_result["user_interacted"] is True
        assert matched_result["feedback_rating"] == 5
        assert matched_result["feedback_notes"] == "Exceptional research match for transformers."

        # Verify student recommendation history
        hist = (await client.get(f"/api/v1/recommendations/history/{student_id}")).json()
        assert hist["total_runs"] >= 1
        assert any(r["run_id"] == run_id for r in hist["runs"])

        # -----------------------------------------------------------------
        # 9. Relevance Judgment & Benchmark Evaluation
        # -----------------------------------------------------------------
        jdg_res = await client.post(
            "/api/v1/evaluation/judgments",
            json={
                "student_id": student_id,
                "faculty_id": top_match["faculty_id"],
                "relevance_grade": 3,
                "benchmark_suite": "integration_eval_suite",
                "notes": "Verified positive relevant candidate for NLP.",
            },
            headers=admin_headers,
        )
        assert jdg_res.status_code == 200
        assert jdg_res.json()["status"] == "created"

        eval_res = await client.post(
            "/api/v1/evaluation/benchmark?benchmark_suite=integration_eval_suite&k_values=1,3",
            headers=admin_headers,
        )
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        assert "hybrid_embedding_scores" in eval_data or "comparison" in eval_data

        # -----------------------------------------------------------------
        # 10. Database Foreign-Key Cascades & Consistency
        # -----------------------------------------------------------------
        # Remove project & skill
        del_proj = await client.delete(
            f"/api/v1/students/{student_id}/projects/{project_id}",
            headers=stu_headers,
        )
        assert del_proj.status_code == 204

        del_skill = await client.delete(
            f"/api/v1/students/{student_id}/skills/{skill_id}",
            headers=stu_headers,
        )
        assert del_skill.status_code == 204

        # Verify student profile clean
        stu_clean = (await client.get(f"/api/v1/students/{student_id}")).json()
        assert len(stu_clean["academic_projects"]) == 0
        assert len(stu_clean["skills_interests"]) == 0

        # Delete student and verify cascading deletion of runs and results
        del_stu = await client.delete(f"/api/v1/students/{student_id}")
        assert del_stu.status_code == 204

        # Confirm student is 404
        assert (await client.get(f"/api/v1/students/{student_id}")).status_code == 404

        # Confirm recommendation run was cascaded
        stmt_run = select(RecommendationRun).where(RecommendationRun.id == uuid.UUID(run_id))
        cascaded_run = (await db_session.execute(stmt_run)).scalars().first()
        assert cascaded_run is None
