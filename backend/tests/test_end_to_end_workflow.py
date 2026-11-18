import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.services.admin_service import admin_service
from backend.app.synthetic.generator import SyntheticConfig


@pytest.mark.asyncio
class TestFullEndToEndWorkflow:
    """Comprehensive end-to-end integration test suite verifying the complete
    user and system lifecycle from data ingestion to recommendation and evaluation.
    """

    async def test_complete_student_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ):
        # -------------------------------------------------------------
        # STEP 1 & 2: Seed synthetic research ecosystem
        # -------------------------------------------------------------
        config = SyntheticConfig(
            num_students=10,
            num_faculty=8,
            num_publications=15,
            seed=42,
        )
        seed_result = await admin_service.seed_synthetic_dataset(
            db_session, config=config, reset_existing=True
        )
        assert seed_result["status"] in ("COMPLETED", "SUCCESS")
        assert seed_result["records_created"] > 0

        # -------------------------------------------------------------
        # STEP 3: Register a new student user and profile
        # -------------------------------------------------------------
        reg_payload = {
            "email": "e2e_student@university.edu",
            "password": "Password123!",
            "role": "STUDENT",
            "first_name": "Elena",
            "last_name": "Rostova",
            "department": "Computer Science",
            "bio": "Undergraduate senior conducting research in multilingual language models.",
            "statement_of_purpose": "I am deeply focused on Natural Language Processing, Transformer architectures, and question-answering systems.",
        }
        reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_res.status_code == 201
        auth_data = reg_res.json()
        token = auth_data["access_token"]
        student_id = auth_data["user"]["student_id"]
        assert student_id is not None
        headers = {"Authorization": f"Bearer {token}"}

        # Verify /auth/me returns registered student
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["first_name"] == "Elena"

        # -------------------------------------------------------------
        # STEP 4: Update student profile with skills and academic project
        # -------------------------------------------------------------
        # 4a. Update profile fields
        update_res = await client.put(
            f"/api/v1/students/{student_id}",
            json={
                "gpa_or_standing": 3.95,
                "graduation_year": 2026,
                "degree_level": "UNDERGRADUATE",
                "availability_status": "SEEKING_ADVISOR",
            },
            headers=headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["gpa_or_standing"] == 3.95

        # 4b. Fetch available taxonomy topics
        topics_res = await client.get("/api/v1/taxonomy/topics")
        assert topics_res.status_code == 200
        topics = topics_res.json()
        assert len(topics) > 0

        # Find NLP topic
        nlp_topic = next((t for t in topics if "Natural Language" in t["name"] or "NLP" in t["slug"].upper()), topics[0])

        # 4c. Add skill to profile
        skill_res = await client.post(
            f"/api/v1/students/{student_id}/skills",
            json={
                "topic_skill_id": nlp_topic["id"],
                "proficiency_level": 5,
                "interest_level": 5,
                "years_experience": 2.0,
            },
            headers=headers,
        )
        assert skill_res.status_code == 201
        assert skill_res.json()["proficiency_level"] == 5

        # 4d. Add academic project to profile
        proj_res = await client.post(
            f"/api/v1/students/{student_id}/projects",
            json={
                "title": "Cross-Lingual Transformer Alignment",
                "description": "Evaluated sentence embeddings and cross-lingual zero-shot transfer on multilingual question answering datasets.",
                "role": "Lead Student Researcher",
                "github_url": "https://github.com/elena/cross-lingual-transformers",
            },
            headers=headers,
        )
        assert proj_res.status_code == 201
        project_id = proj_res.json()["id"]

        # Verify student details now include project and skill
        detail_res = await client.get(f"/api/v1/students/{student_id}")
        assert detail_res.status_code == 200
        student_details = detail_res.json()
        assert len(student_details["skills_interests"]) >= 1
        assert len(student_details["academic_projects"]) >= 1

        # -------------------------------------------------------------
        # STEP 5: Generate and synchronize embeddings
        # -------------------------------------------------------------
        sync_res = await client.post(
            "/api/v1/embeddings/sync", headers=admin_auth_headers
        )
        assert sync_res.status_code == 200
        sync_data = sync_res.json()
        assert sync_data["status"] == "sync_complete"
        assert sync_data["faculty_embedded"] >= 8

        # Verify embedding stats
        stats_res = await client.get(
            "/api/v1/embeddings/stats", headers=admin_auth_headers
        )
        assert stats_res.status_code == 200
        stats_data = stats_res.json()
        assert stats_data.get("active_dimension", stats_data.get("embedding_dimension")) == 384

        # -------------------------------------------------------------
        # STEP 6: Request AI Recommendations
        # -------------------------------------------------------------
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
                    "only_accepting_students": False,
                },
            },
            headers=headers,
        )
        assert rec_res.status_code == 200
        rec_data = rec_res.json()
        assert rec_data["student_id"] == student_id
        assert len(rec_data["recommendations"]) > 0

        # -------------------------------------------------------------
        # STEP 7: Inspect Ranked Results, Explanations & Evidence
        # -------------------------------------------------------------
        top_match = rec_data["recommendations"][0]
        assert top_match["rank_position"] == 1
        assert 0.0 <= top_match["overall_score"] <= 1.0

        # Check 4-signal breakdown
        breakdown = top_match["score_breakdown"]
        assert 0.0 <= breakdown["research_interest_score"] <= 1.0
        assert 0.0 <= breakdown["project_research_score"] <= 1.0
        assert 0.0 <= breakdown["publication_relevance_score"] <= 1.0
        assert 0.0 <= breakdown["skill_compatibility_score"] <= 1.0

        # Check explanation summary is grounded and non-empty
        assert len(top_match["explanation_summary"]) > 10

        # Check relevant publications evidence
        assert isinstance(top_match["top_publications"], list)

        # -------------------------------------------------------------
        # STEP 7b: Retrieve Faculty Profile & Publication Evidence
        # -------------------------------------------------------------
        fac_detail_res = await client.get(f"/api/v1/faculty/{top_match['faculty_id']}")
        assert fac_detail_res.status_code == 200
        fac_detail = fac_detail_res.json()
        assert fac_detail["id"] == top_match["faculty_id"]
        assert len(fac_detail["skills_expertise"]) >= 1

        # -------------------------------------------------------------
        # STEP 8: Submit recommendation feedback rating & verify persistence
        # -------------------------------------------------------------
        run_id = rec_data["run_id"]
        feedback_res = await client.post(
            f"/api/v1/recommendations/runs/{run_id}/results/{top_match['faculty_id']}/feedback",
            params={"rating": 5, "notes": "Highly relevant faculty member."},
            headers=headers,
        )
        assert feedback_res.status_code == 200

        # Verify feedback in run details
        run_detail_res = await client.get(f"/api/v1/recommendations/runs/{run_id}")
        assert run_detail_res.status_code == 200
        run_results = run_detail_res.json()["results"]
        matched_result = next(r for r in run_results if r["faculty_id"] == top_match["faculty_id"])
        assert matched_result["user_interacted"] is True
        assert matched_result["feedback_rating"] == 5
        assert matched_result["feedback_notes"] == "Highly relevant faculty member."

        # Verify recommendation history
        history_res = await client.get(f"/api/v1/recommendations/history/{student_id}")
        assert history_res.status_code == 200
        assert history_res.json()["total_runs"] >= 1
        assert any(r["run_id"] == run_id for r in history_res.json()["runs"])

        # -------------------------------------------------------------
        # STEP 9: Run offline benchmark evaluation
        # -------------------------------------------------------------
        # 9a. Create custom relevance judgment
        custom_jdg_res = await client.post("/api/v1/evaluation/judgments", json={
            "student_id": student_id,
            "faculty_id": top_match["faculty_id"],
            "relevance_grade": 3,
            "benchmark_suite": "e2e_student_suite",
            "notes": "Verified relevant for benchmark evaluation.",
        }, headers=admin_auth_headers)
        assert custom_jdg_res.status_code == 200
        assert custom_jdg_res.json()["status"] in ("created", "updated")

        # 9b. Execute benchmark on custom suite
        eval_res = await client.post(
            "/api/v1/evaluation/benchmark?benchmark_suite=e2e_student_suite&k_values=1,5",
            headers=admin_auth_headers,
        )
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        assert "hybrid_embedding_scores" in eval_data or "comparison" in eval_data

        # -------------------------------------------------------------
        # STEP 10: Clean up student project and skill
        # -------------------------------------------------------------
        del_proj_res = await client.delete(
            f"/api/v1/students/{student_id}/projects/{project_id}",
            headers=headers,
        )
        assert del_proj_res.status_code == 204

        skill_id = skill_res.json()["id"]
        del_skill_res = await client.delete(
            f"/api/v1/students/{student_id}/skills/{skill_id}",
            headers=headers,
        )
        assert del_skill_res.status_code == 204

        # Verify both project and skill are removed
        post_del_res = await client.get(f"/api/v1/students/{student_id}")
        assert post_del_res.status_code == 200
        assert len(post_del_res.json()["academic_projects"]) == 0
        assert len(post_del_res.json()["skills_interests"]) == 0


@pytest.mark.asyncio
class TestSecurityAndFailureScenarios:
    """Rigorous security, validation, and error-handling tests."""

    async def test_unauthorized_endpoints(self, client: AsyncClient):
        # Accessing /auth/me with no token returns 401
        res = await client.get("/api/v1/auth/me")
        assert res.status_code == 401

        # Accessing /auth/me with bogus token returns 401
        bad_token_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.payload"},
        )
        assert bad_token_res.status_code == 401

    async def test_student_forbidden_from_admin_operations(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        # Create student user and token
        student_user = User(
            id=uuid.uuid4(),
            email="regular_student@test.edu",
            hashed_password="hashed_pass",
            role="STUDENT",
            is_active=True,
        )
        db_session.add(student_user)
        await db_session.commit()

        token = create_access_token(subject=student_user.id, role="STUDENT")

        # Attempting to call reset-synthetic as STUDENT must return 403
        res = await client.post(
            "/api/v1/admin/reset-synthetic",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert "Administrative privileges required" in res.json()["detail"]

    async def test_admin_token_allowed_admin_operations(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        admin_user = User(
            id=uuid.uuid4(),
            email="admin_test@test.edu",
            hashed_password="hashed_pass",
            role="ADMIN",
            is_active=True,
        )
        db_session.add(admin_user)
        await db_session.commit()

        admin_token = create_access_token(subject=admin_user.id, role="ADMIN")

        res = await client.get(
            "/api/v1/admin/data-counts",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res.status_code == 200

    async def test_invalid_uuid_returns_404(self, client: AsyncClient):
        random_uuid = uuid.uuid4()
        res = await client.get(f"/api/v1/students/{random_uuid}")
        assert res.status_code == 404

        res_fac = await client.get(f"/api/v1/faculty/{random_uuid}")
        assert res_fac.status_code == 404

    async def test_validation_errors_formatted_as_rfc7807(self, client: AsyncClient):
        # Missing required first_name and email
        res = await client.post("/api/v1/auth/register", json={"password": "123"})
        assert res.status_code == 422
        problem = res.json()
        assert problem["code"] == "REQUEST_VALIDATION_FAILED"
        assert len(problem["invalid_params"]) > 0

    async def test_rate_limiter_protects_login(self, client: AsyncClient):
        # Rapid-fire attempts on auth
        from backend.app.core.rate_limit import auth_limiter
        # Force limiter to threshold for a mock key
        key = "auth:mock_test_ip"
        for _ in range(25):
            auth_limiter.is_rate_limited(key)
        assert auth_limiter.is_rate_limited(key) is True
        auth_limiter.reset()
