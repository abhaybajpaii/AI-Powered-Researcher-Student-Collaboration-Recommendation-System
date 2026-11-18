import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import timedelta
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.models.provenance import DataSource, ImportJob
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_validate_records_endpoint(
    client: AsyncClient, admin_auth_headers: dict[str, str]
):
    valid_payload = {
        "topics": [{"name": "Test Topic", "category": "DOMAIN"}],
        "faculty": [],
        "students": [],
        "publications": [],
        "relevance_judgments": [],
    }
    res = await client.post(
        "/api/v1/admin/validate-records",
        json=valid_payload,
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["summary"]["topics"] == 1

    invalid_payload = {
        "topics": [{"name": "X", "category": "INVALID"}],  # name too short
    }
    invalid_res = await client.post(
        "/api/v1/admin/validate-records",
        json=invalid_payload,
        headers=admin_auth_headers,
    )
    assert invalid_res.status_code == 200
    assert invalid_res.json()["valid"] is False


@pytest.mark.asyncio
async def test_seed_synthetic_and_data_counts(
    client: AsyncClient, admin_auth_headers: dict[str, str]
):
    admin_headers = admin_auth_headers

    seed_payload = {
        "config": {
            "seed": 42,
            "num_students": 10,
            "num_faculty": 8,
            "num_publications": 15,
            "num_relevance_judgments": 10,
        },
        "reset_existing": True,
    }

    # 1. Seed Synthetic Dataset
    seed_res = await client.post("/api/v1/admin/seed-synthetic", json=seed_payload, headers=admin_headers)
    assert seed_res.status_code == 200
    seed_data = seed_res.json()
    assert seed_data["status"] == "COMPLETED"
    assert seed_data["records_created"] > 0
    job_id = seed_data["job_id"]

    # 2. Check Data Counts by Entity and Mode
    counts_res = await client.get(
        "/api/v1/admin/data-counts", headers=admin_headers
    )
    assert counts_res.status_code == 200
    counts = counts_res.json()
    assert counts["by_entity"]["students"]["synthetic"] == 10
    assert counts["by_entity"]["faculty"]["synthetic"] == 8
    assert counts["by_entity"]["publications"]["synthetic"] == 15
    assert counts["summary"]["synthetic_records"] > 0

    # 3. Check Import Job Details
    job_res = await client.get(f"/api/v1/admin/import-jobs/{job_id}", headers=admin_headers)
    assert job_res.status_code == 200
    job_details = job_res.json()
    assert job_details["status"] == "COMPLETED"
    assert job_details["data_source_type"] == "SYNTHETIC"

    # 4. Check Import Jobs List
    list_jobs_res = await client.get(
        "/api/v1/admin/import-jobs?page=1&page_size=10", headers=admin_headers
    )
    assert list_jobs_res.status_code == 200
    assert list_jobs_res.json()["total"] >= 1

    # 5. Repeated Seeding Idempotency (running without reset should update or keep counts, not explode)
    repeat_res = await client.post("/api/v1/admin/seed-synthetic", json={"config": seed_payload["config"], "reset_existing": False}, headers=admin_headers)
    assert repeat_res.status_code == 200
    repeat_data = repeat_res.json()
    # Deduplication should update existing, creating 0 or minimal new publications
    assert repeat_data["status"] == "COMPLETED"

    # Check publication count is still 15 (no duplicate publications created)
    counts_res2 = await client.get(
        "/api/v1/admin/data-counts", headers=admin_headers
    )
    assert counts_res2.json()["by_entity"]["publications"]["total"] == 15

    # 6. Reset Synthetic Data
    reset_res = await client.post("/api/v1/admin/reset-synthetic", headers=admin_headers)
    assert reset_res.status_code == 200

    # Verify counts after reset
    counts_after_reset = await client.get(
        "/api/v1/admin/data-counts", headers=admin_headers
    )
    assert counts_after_reset.json()["by_entity"]["students"]["synthetic"] == 0
    assert counts_after_reset.json()["by_entity"]["faculty"]["synthetic"] == 0
    assert counts_after_reset.json()["by_entity"]["publications"]["synthetic"] == 0


@pytest.mark.asyncio
async def test_admin_routes_reject_legacy_api_keys(client: AsyncClient):
    for key in ("dev_admin_secret_key_2026", settings.SECRET_KEY):
        response = await client.post(
            "/api/v1/admin/seed-synthetic",
            headers={"X-Admin-Key": key},
            json={"config": {"num_students": 5, "num_faculty": 5, "num_publications": 0}},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_import_job_retry_does_not_report_success_or_change_job_state(
    client: AsyncClient,
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    source = DataSource(
        name=f"retry-test-{uuid.uuid4().hex}",
        source_type="OPENALEX",
    )
    job = ImportJob(data_source=source, status="FAILED")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await client.post(
        f"/api/v1/scholarly/jobs/{job.id}/retry",
        headers=admin_auth_headers,
    )

    assert response.status_code == 501
    assert "not implemented" in response.json()["detail"].lower()
    await db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.completed_at is None


@pytest.mark.asyncio
async def test_import_job_routes_require_admin_authentication(client: AsyncClient):
    unauthenticated_list = await client.get("/api/v1/admin/import-jobs")
    unauthenticated_detail = await client.get(
        f"/api/v1/admin/import-jobs/{uuid.uuid4()}"
    )
    assert unauthenticated_list.status_code == 401
    assert unauthenticated_detail.status_code == 401


@pytest.mark.asyncio
async def test_admin_read_and_management_endpoints_reject_anonymous_users(
    client: AsyncClient,
):
    protected_gets = (
        "/api/v1/admin/data-counts",
        "/api/v1/scholarly/summary",
        "/api/v1/scholarly/jobs",
        "/api/v1/embeddings/stats",
        f"/api/v1/embeddings/entity/STUDENT/{uuid.uuid4()}",
    )
    for endpoint in protected_gets:
        response = await client.get(endpoint)
        assert response.status_code == 401, endpoint

    protected_posts = (
        ("/api/v1/admin/validate-records", {}),
        ("/api/v1/embeddings/sync", None),
        ("/api/v1/evaluation/benchmark", None),
        (
            "/api/v1/evaluation/judgments",
            {
                "student_id": str(uuid.uuid4()),
                "faculty_id": str(uuid.uuid4()),
                "relevance_grade": 1,
            },
        ),
    )
    for endpoint, body in protected_posts:
        response = await client.post(endpoint, json=body)
        assert response.status_code == 401, endpoint


@pytest.mark.asyncio
async def test_inactive_admin_cannot_access_protected_admin_routes(
    client: AsyncClient, db_session: AsyncSession
):
    inactive_admin = User(
        id=uuid.uuid4(),
        email=f"inactive_admin_{uuid.uuid4().hex[:8]}@university.edu",
        hashed_password="unused_test_hash",
        role="ADMIN",
        is_active=False,
    )
    db_session.add(inactive_admin)
    await db_session.commit()
    token = create_access_token(subject=inactive_admin.id, role="ADMIN")

    response = await client.get(
        "/api/v1/admin/import-jobs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_admin_roles_cannot_access_admin_data(
    client: AsyncClient,
    sample_student_user: User,
    sample_faculty_user: User,
):
    for user in (sample_student_user, sample_faculty_user):
        token = create_access_token(subject=user.id, role=user.role)
        response = await client.get(
            "/api/v1/admin/data-counts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_and_expired_tokens_cannot_access_admin_data(
    client: AsyncClient,
):
    expired_token = create_access_token(
        subject=uuid.uuid4(),
        role="ADMIN",
        expires_delta=timedelta(seconds=-1),
    )
    for token in ("not-a-valid-token", expired_token):
        response = await client.get(
            "/api/v1/admin/data-counts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
