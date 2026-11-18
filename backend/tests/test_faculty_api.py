import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.faculty import Faculty
from backend.app.models.taxonomy import FacultySkillExpertise, TopicSkill
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_faculty_crud_lifecycle(client: AsyncClient, sample_faculty_user):
    # 1. Create Faculty
    create_payload = {
        "user_id": str(sample_faculty_user.id),
        "faculty_number": "FAC-2026-001",
        "first_name": "Alan",
        "last_name": "Turing",
        "department": "Computer Science",
        "title_rank": "FULL_PROFESSOR",
        "office_location": "Turing Hall 401",
        "website_url": "https://turing.cs.edu",
        "lab_name": "Foundations of AI & Computation Lab",
        "accepting_students": True,
        "max_capacity": 6,
        "current_student_count": 2,
        "bio": "Foundational work on computability and machine intelligence.",
    }
    create_res = await client.post("/api/v1/faculty", json=create_payload)
    assert create_res.status_code == 201
    created_faculty = create_res.json()
    faculty_id = created_faculty["id"]
    assert created_faculty["first_name"] == "Alan"
    assert created_faculty["accepting_students"] is True

    # 2. Get Faculty by ID
    get_res = await client.get(f"/api/v1/faculty/{faculty_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == faculty_id

    # 3. List Faculty with Capacity & Availability Filters
    list_res = await client.get(
        "/api/v1/faculty?department=Computer Science&accepting_students=true&min_capacity=2"
    )
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(f["id"] == faculty_id for f in list_data["items"])

    # 4. Update Faculty
    update_payload = {
        "current_student_count": 3,
        "office_location": "Turing Hall 402",
    }
    put_res = await client.put(f"/api/v1/faculty/{faculty_id}", json=update_payload)
    assert put_res.status_code == 200
    assert put_res.json()["current_student_count"] == 3
    assert put_res.json()["office_location"] == "Turing Hall 402"

    # 5. Duplicate Profile Prevention (409 Conflict)
    duplicate_res = await client.post("/api/v1/faculty", json=create_payload)
    assert duplicate_res.status_code == 409
    assert duplicate_res.json()["code"] == "FACULTY_PROFILE_EXISTS"

    # 6. Delete Faculty
    del_res = await client.delete(f"/api/v1/faculty/{faculty_id}")
    assert del_res.status_code == 204

    # 7. Verify Deleted
    verify_res = await client.get(f"/api/v1/faculty/{faculty_id}")
    assert verify_res.status_code == 404


# -----------------------------------------------------------------------------
# Faculty Directory Search Test Suite
# -----------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def populated_search_faculty(db_session: AsyncSession):
    """Seed three distinct faculty profiles with taxonomy skills for search validation."""
    topic_ml = TopicSkill(
        id=uuid.uuid4(),
        name="Machine Learning",
        slug="machine-learning",
        category="ARTIFICIAL_INTELLIGENCE",
    )
    topic_algo = TopicSkill(
        id=uuid.uuid4(),
        name="Algorithms",
        slug="algorithms",
        category="COMPUTER_SCIENCE",
    )
    topic_dsp = TopicSkill(
        id=uuid.uuid4(),
        name="Signal Processing",
        slug="signal-processing",
        category="ELECTRICAL_ENGINEERING",
    )
    db_session.add_all([topic_ml, topic_algo, topic_dsp])
    await db_session.flush()

    user1 = User(
        id=uuid.uuid4(),
        email=f"turing_{uuid.uuid4().hex[:6]}@university.edu",
        hashed_password="pw",
        role="FACULTY",
        is_active=True,
    )
    user2 = User(
        id=uuid.uuid4(),
        email=f"lovelace_{uuid.uuid4().hex[:6]}@university.edu",
        hashed_password="pw",
        role="FACULTY",
        is_active=True,
    )
    user3 = User(
        id=uuid.uuid4(),
        email=f"shannon_{uuid.uuid4().hex[:6]}@university.edu",
        hashed_password="pw",
        role="FACULTY",
        is_active=True,
    )
    db_session.add_all([user1, user2, user3])
    await db_session.flush()

    # Faculty 1: Alan Turing (Computer Science, open capacity 4, accepting)
    f1 = Faculty(
        id=uuid.uuid4(),
        user_id=user1.id,
        first_name="Alan",
        last_name="Turing",
        department="Computer Science",
        title_rank="FULL_PROFESSOR",
        lab_name="Foundations of AI Lab",
        accepting_students=True,
        max_capacity=6,
        current_student_count=2,
        bio="Pioneering research in theoretical computation and neural intelligence.",
    )
    # Faculty 2: Ada Lovelace (Mathematics, open capacity 3, accepting)
    f2 = Faculty(
        id=uuid.uuid4(),
        user_id=user2.id,
        first_name="Ada",
        last_name="Lovelace",
        department="Mathematics",
        title_rank="ASSOCIATE_PROFESSOR",
        lab_name="Analytical Engines Group",
        accepting_students=True,
        max_capacity=4,
        current_student_count=1,
        bio="Algorithmic computation and mathematical program verification.",
    )
    # Faculty 3: Claude Shannon (Electrical Engineering, open capacity 0, not accepting)
    f3 = Faculty(
        id=uuid.uuid4(),
        user_id=user3.id,
        first_name="Claude",
        last_name="Shannon",
        department="Electrical Engineering",
        title_rank="FULL_PROFESSOR",
        lab_name="Information Theory Lab",
        accepting_students=False,
        max_capacity=5,
        current_student_count=5,
        bio="Entropy measures and mathematical theory of communication.",
    )
    db_session.add_all([f1, f2, f3])
    await db_session.flush()

    e1 = FacultySkillExpertise(
        id=uuid.uuid4(),
        faculty_id=f1.id,
        topic_skill_id=topic_ml.id,
        expertise_level=5,
        is_primary_focus=True,
    )
    e2 = FacultySkillExpertise(
        id=uuid.uuid4(),
        faculty_id=f2.id,
        topic_skill_id=topic_algo.id,
        expertise_level=5,
        is_primary_focus=True,
    )
    e3 = FacultySkillExpertise(
        id=uuid.uuid4(),
        faculty_id=f3.id,
        topic_skill_id=topic_dsp.id,
        expertise_level=5,
        is_primary_focus=True,
    )
    db_session.add_all([e1, e2, e3])
    await db_session.commit()

    return {
        "turing": f1,
        "lovelace": f2,
        "shannon": f3,
    }


@pytest.mark.asyncio
async def test_faculty_search_by_name(client: AsyncClient, populated_search_faculty):
    facs = populated_search_faculty
    turing_id = str(facs["turing"].id)
    lovelace_id = str(facs["lovelace"].id)
    shannon_id = str(facs["shannon"].id)

    # 1. Search by last name
    res1 = await client.get("/api/v1/faculty?search=Turing")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] == 1
    assert data1["items"][0]["id"] == turing_id

    # 2. Search by first name
    res2 = await client.get("/api/v1/faculty?search=Ada")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total"] == 1
    assert data2["items"][0]["id"] == lovelace_id

    # 3. Search by full name with space
    res3 = await client.get("/api/v1/faculty?search=Claude Shannon")
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["total"] == 1
    assert data3["items"][0]["id"] == shannon_id


@pytest.mark.asyncio
async def test_faculty_search_by_department(client: AsyncClient, populated_search_faculty):
    facs = populated_search_faculty
    lovelace_id = str(facs["lovelace"].id)

    res = await client.get("/api/v1/faculty?search=Mathematics")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == lovelace_id


@pytest.mark.asyncio
async def test_faculty_search_by_research_interests_and_expertise(client: AsyncClient, populated_search_faculty):
    facs = populated_search_faculty
    turing_id = str(facs["turing"].id)
    shannon_id = str(facs["shannon"].id)

    # Search in bio (research statement)
    res_bio = await client.get("/api/v1/faculty?search=entropy")
    assert res_bio.status_code == 200
    data_bio = res_bio.json()
    assert data_bio["total"] == 1
    assert data_bio["items"][0]["id"] == shannon_id

    # Search in associated taxonomy skill name
    res_skill = await client.get("/api/v1/faculty?search=Machine Learning")
    assert res_skill.status_code == 200
    data_skill = res_skill.json()
    assert data_skill["total"] == 1
    assert data_skill["items"][0]["id"] == turing_id


@pytest.mark.asyncio
async def test_faculty_search_case_insensitivity(client: AsyncClient, populated_search_faculty):
    facs = populated_search_faculty
    turing_id = str(facs["turing"].id)
    lovelace_id = str(facs["lovelace"].id)

    res1 = await client.get("/api/v1/faculty?search=tUrInG")
    assert res1.status_code == 200
    assert res1.json()["total"] == 1
    assert res1.json()["items"][0]["id"] == turing_id

    res2 = await client.get("/api/v1/faculty?search=mAtHeMaTiCs")
    assert res2.status_code == 200
    assert res2.json()["total"] == 1
    assert res2.json()["items"][0]["id"] == lovelace_id


@pytest.mark.asyncio
async def test_faculty_search_partial_word_matching(client: AsyncClient, populated_search_faculty):
    facs = populated_search_faculty
    turing_id = str(facs["turing"].id)
    lovelace_id = str(facs["lovelace"].id)

    # "comput" matches "Computer Science" and "computation"
    res = await client.get("/api/v1/faculty?search=comput")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    matched_ids = {item["id"] for item in data["items"]}
    assert turing_id in matched_ids
    assert lovelace_id in matched_ids


@pytest.mark.asyncio
async def test_faculty_search_empty_and_whitespace(client: AsyncClient, populated_search_faculty):
    # Empty string should behave as no search filter
    res_empty = await client.get("/api/v1/faculty?search=")
    assert res_empty.status_code == 200
    assert res_empty.json()["total"] == 3

    # Whitespace-only string should behave as no search filter
    res_ws = await client.get("/api/v1/faculty?search=%20%20%20")
    assert res_ws.status_code == 200
    assert res_ws.json()["total"] == 3


@pytest.mark.asyncio
async def test_faculty_search_combined_with_department_filter(client: AsyncClient, populated_search_faculty):
    facs = populated_search_faculty
    turing_id = str(facs["turing"].id)

    # "computation" is in bio of both Turing and Lovelace, but department=Computer Science narrows to Turing
    res = await client.get("/api/v1/faculty?search=computation&department=Computer Science")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == turing_id


@pytest.mark.asyncio
async def test_faculty_search_combined_with_pagination(client: AsyncClient, populated_search_faculty):
    # "computation" matches 2 faculty members (Turing and Lovelace)
    # Page 1, page_size 1
    res_p1 = await client.get("/api/v1/faculty?search=computation&page=1&page_size=1")
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert data_p1["total"] == 2
    assert len(data_p1["items"]) == 1
    assert data_p1["page"] == 1
    assert data_p1["page_size"] == 1
    assert data_p1["total_pages"] == 2

    # Page 2, page_size 1
    res_p2 = await client.get("/api/v1/faculty?search=computation&page=2&page_size=1")
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    assert data_p2["total"] == 2
    assert len(data_p2["items"]) == 1
    assert data_p2["page"] == 2
    assert data_p2["page_size"] == 1
    assert data_p2["total_pages"] == 2

    # Items on page 1 and page 2 must be different
    assert data_p1["items"][0]["id"] != data_p2["items"][0]["id"]


@pytest.mark.asyncio
async def test_faculty_search_no_match(client: AsyncClient, populated_search_faculty):
    res = await client.get("/api/v1/faculty?search=AstrophysicsNonExistentQuery999")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1
    assert data["total_pages"] == 0


@pytest.mark.asyncio
async def test_existing_faculty_filters_continue_to_work(client: AsyncClient, populated_search_faculty):
    facs = populated_search_faculty
    turing_id = str(facs["turing"].id)
    shannon_id = str(facs["shannon"].id)

    # 1. accepting_students filter (Turing and Lovelace are True, Shannon is False)
    res_accepting = await client.get("/api/v1/faculty?accepting_students=true")
    assert res_accepting.status_code == 200
    data_accepting = res_accepting.json()
    assert data_accepting["total"] == 2
    assert all(f["accepting_students"] is True for f in data_accepting["items"])

    # 2. min_capacity filter (Turing open capacity = 4, Lovelace = 3, Shannon = 0)
    res_cap = await client.get("/api/v1/faculty?min_capacity=4")
    assert res_cap.status_code == 200
    data_cap = res_cap.json()
    assert data_cap["total"] == 1
    assert data_cap["items"][0]["id"] == turing_id

    # 3. department filter alone
    res_dept = await client.get("/api/v1/faculty?department=Electrical Engineering")
    assert res_dept.status_code == 200
    data_dept = res_dept.json()
    assert data_dept["total"] == 1
    assert data_dept["items"][0]["id"] == shannon_id

