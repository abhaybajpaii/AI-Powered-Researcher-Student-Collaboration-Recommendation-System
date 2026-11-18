import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validation_missing_required_fields(client: AsyncClient):
    # Sending empty body to student creation endpoint
    response = await client.post("/api/v1/students", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "REQUEST_VALIDATION_FAILED"
    assert "invalid_params" in data
    assert len(data["invalid_params"]) > 0


@pytest.mark.asyncio
async def test_validation_invalid_gpa(client: AsyncClient, sample_student_user):
    payload = {
        "user_id": str(sample_student_user.id),
        "first_name": "Ada",
        "last_name": "Lovelace",
        "department": "Computer Science",
        "degree_level": "UNDERGRADUATE",
        "statement_of_purpose": "Passionate about computing architectures.",
        "gpa_or_standing": 5.5,  # Invalid: max is 4.0
    }
    response = await client.post("/api/v1/students", json=payload)
    assert response.status_code == 422
    data = response.json()
    invalid_fields = [p["field"] for p in data["invalid_params"]]
    assert "gpa_or_standing" in invalid_fields


@pytest.mark.asyncio
async def test_not_found_response_format(client: AsyncClient):
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/students/{fake_uuid}")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "STUDENT_NOT_FOUND"
    assert data["title"] == "Resource Not Found"
    assert "detail" in data
