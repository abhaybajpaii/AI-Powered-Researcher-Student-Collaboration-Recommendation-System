import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_student_crud_lifecycle(client: AsyncClient, sample_student_user):
    # 1. Create Student
    create_payload = {
        "user_id": str(sample_student_user.id),
        "student_number": "STU-2026-001",
        "first_name": "Grace",
        "last_name": "Hopper",
        "department": "Computer Science",
        "degree_level": "PHD",
        "gpa_or_standing": 3.95,
        "graduation_year": 2027,
        "bio": "Compiler design researcher",
        "statement_of_purpose": "I want to work on novel compiler optimizations and programming languages.",
        "availability_status": "SEEKING_ADVISOR",
    }
    create_res = await client.post("/api/v1/students", json=create_payload)
    assert create_res.status_code == 201
    created_student = create_res.json()
    student_id = created_student["id"]
    assert created_student["first_name"] == "Grace"
    assert created_student["degree_level"] == "PHD"

    # 2. Get Student by ID
    get_res = await client.get(f"/api/v1/students/{student_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == student_id

    # 3. List Students with Filter
    list_res = await client.get("/api/v1/students?department=Computer Science&page=1&page_size=10")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(s["id"] == student_id for s in list_data["items"])

    # 4. Update Student
    update_payload = {
        "bio": "Pioneer of compiled programming languages",
        "gpa_or_standing": 4.0,
    }
    put_res = await client.put(f"/api/v1/students/{student_id}", json=update_payload)
    assert put_res.status_code == 200
    assert put_res.json()["bio"] == "Pioneer of compiled programming languages"
    assert put_res.json()["gpa_or_standing"] == 4.0

    # 5. Duplicate Profile Prevention (409 Conflict)
    duplicate_res = await client.post("/api/v1/students", json=create_payload)
    assert duplicate_res.status_code == 409
    assert duplicate_res.json()["code"] == "STUDENT_PROFILE_EXISTS"

    # 6. Delete Student
    del_res = await client.delete(f"/api/v1/students/{student_id}")
    assert del_res.status_code == 204

    # 7. Verify Deleted
    verify_res = await client.get(f"/api/v1/students/{student_id}")
    assert verify_res.status_code == 404
