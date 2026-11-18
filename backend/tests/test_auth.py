import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.security import get_password_hash
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_auth_register_and_login(client: AsyncClient, db_session: AsyncSession):
    # 1. Register a student
    reg_payload = {
        "email": "new_student@university.edu",
        "password": "securepassword123",
        "role": "STUDENT",
        "first_name": "Jordan",
        "last_name": "Lee",
        "department": "Computer Science",
        "statement_of_purpose": "Exploring reinforcement learning.",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new_student@university.edu"
    assert data["user"]["role"] == "STUDENT"
    assert data["user"]["student_id"] is not None

    token = data["access_token"]

    # 2. Check /me with token
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "new_student@university.edu"
    assert me_data["first_name"] == "Jordan"

    # 3. Check login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "new_student@university.edu", "password": "securepassword123"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 4. Check wrong password
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "new_student@university.edu", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 401


@pytest.mark.asyncio
async def test_auth_unauthorized(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["ADMIN", "FACULTY"])
async def test_public_registration_rejects_non_student_roles(
    client: AsyncClient,
    db_session: AsyncSession,
    role: str,
):
    email = f"attempted_{role.lower()}@university.edu"
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "securepassword123",
            "role": role,
            "first_name": "Test",
            "last_name": "Account",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Public registration is limited to STUDENT accounts."
    assert (
        await db_session.execute(select(User).where(User.email == email))
    ).scalars().first() is None
