import uuid
from datetime import date
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.faculty import Faculty
from backend.app.models.taxonomy import TopicSkill, StudentSkillInterest, FacultySkillExpertise
from backend.app.models.publication import Publication, PublicationAuthorship
from backend.app.models.recommendation import RecommendationRun, RecommendationResult
from backend.app.models.evaluation import RelevanceJudgment
from backend.app.models.embedding import EmbeddingRecord

@pytest.mark.asyncio
async def test_faculty_deletion_preserves_publication_authorship(db_session):
    """Regression test: Deleting a faculty member must NOT delete the publication or its authorship link."""
    # 1. Create faculty
    fac_user = User(
        email=f"prof_{uuid.uuid4().hex[:6]}@univ.edu",
        hashed_password="pw",
        role="FACULTY",
    )
    db_session.add(fac_user)
    await db_session.commit()
    await db_session.refresh(fac_user)

    faculty = Faculty(
        user_id=fac_user.id,
        first_name="Ada",
        last_name="Lovelace",
        department="Computer Science",
    )
    db_session.add(faculty)
    await db_session.commit()
    await db_session.refresh(faculty)
    faculty_id = faculty.id

    # 2. Create publication and authorship
    pub = Publication(
        title=f"Analytical Engine Notes {uuid.uuid4().hex[:6]}",
        abstract="Notes on the engine.",
        title_hash=uuid.uuid4().hex[:32],
    )
    db_session.add(pub)
    await db_session.commit()
    await db_session.refresh(pub)
    pub_id = pub.id

    authorship = PublicationAuthorship(
        publication_id=pub_id,
        faculty_id=faculty_id,
        raw_author_name="Ada Lovelace",
        is_corresponding=True,
    )
    db_session.add(authorship)
    await db_session.commit()
    await db_session.refresh(authorship)
    authorship_id = authorship.id

    # 3. Delete faculty
    await db_session.delete(faculty)
    await db_session.commit()

    # 4. Verify publication and authorship still exist
    pub_check = await db_session.get(Publication, pub_id)
    assert pub_check is not None, "Publication was unexpectedly deleted when faculty was deleted!"

    auth_check = await db_session.get(PublicationAuthorship, authorship_id)
    assert auth_check is not None, "PublicationAuthorship was unexpectedly deleted by ORM cascade!"
    assert auth_check.raw_author_name == "Ada Lovelace"


@pytest.mark.asyncio
async def test_composite_unique_constraints(db_session):
    """Regression test: Composite unique constraints on junction/association tables."""
    # Create base entities
    u_stud = User(email=f"stud_{uuid.uuid4().hex[:6]}@univ.edu", hashed_password="pw", role="STUDENT")
    u_fac = User(email=f"fac_{uuid.uuid4().hex[:6]}@univ.edu", hashed_password="pw", role="FACULTY")
    db_session.add_all([u_stud, u_fac])
    await db_session.commit()

    student = Student(user_id=u_stud.id, first_name="A", last_name="B", department="CS", statement_of_purpose="SOP")
    faculty = Faculty(user_id=u_fac.id, first_name="C", last_name="D", department="CS")
    topic = TopicSkill(name=f"Topic_{uuid.uuid4().hex[:6]}", slug=f"slug-{uuid.uuid4().hex[:6]}", category="RESEARCH_TOPIC")
    db_session.add_all([student, faculty, topic])
    await db_session.commit()

    # StudentSkill duplicate
    s_id = student.id
    f_id = faculty.id
    t_id = topic.id

    ss1 = StudentSkillInterest(student_id=s_id, topic_skill_id=t_id, proficiency_level=3)
    db_session.add(ss1)
    await db_session.commit()

    ss2 = StudentSkillInterest(student_id=s_id, topic_skill_id=t_id, proficiency_level=4)
    db_session.add(ss2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # RecommendationResult duplicate for same run & faculty
    run = RecommendationRun(student_id=s_id, algorithm_version="1.0", parameters={}, execution_time_ms=10.0)
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    rr1 = RecommendationResult(
        run_id=run.id, faculty_id=f_id, rank_position=1, overall_score=0.9,
        semantic_score=0.9, skill_score=0.9, project_score=0.9, explanation_data={}
    )
    db_session.add(rr1)
    await db_session.commit()

    rr2 = RecommendationResult(
        run_id=run.id, faculty_id=f_id, rank_position=2, overall_score=0.8,
        semantic_score=0.8, skill_score=0.8, project_score=0.8, explanation_data={}
    )
    db_session.add(rr2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_transaction_atomic_rollback(db_session):
    """Regression test: Mid-operation failure rolls back all partial operations atomically."""
    user_email = f"tx_fail_{uuid.uuid4().hex[:6]}@univ.edu"
    u = User(email=user_email, hashed_password="pw", role="STUDENT")
    db_session.add(u)
    await db_session.flush()

    # Add duplicate email in same session to force constraint failure
    u_bad = User(email=user_email, hashed_password="pw", role="STUDENT")
    db_session.add(u_bad)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # Verify u was NOT persisted
    res = await db_session.execute(select(User).where(User.email == user_email))
    assert res.first() is None, "User should have rolled back completely!"

