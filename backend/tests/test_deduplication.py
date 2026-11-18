import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.ingestion.deduplication import (
    find_existing_publication,
    find_existing_topic,
    find_existing_user,
)
from backend.app.models.publication import Publication
from backend.app.models.taxonomy import TopicSkill
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_find_existing_publication(db_session: AsyncSession):
    pub = Publication(
        id=uuid.uuid4(),
        title="Sample Deduplication Paper",
        abstract="Abstract testing deduplication.",
        publication_year=2025,
        doi="10.synthetic/dedup/123",
        title_hash="hash_dedup_12345",
    )
    db_session.add(pub)
    await db_session.commit()

    # Search by DOI
    found_by_doi = await find_existing_publication(db_session, doi="10.synthetic/dedup/123")
    assert found_by_doi is not None
    assert found_by_doi.id == pub.id

    # Search by title hash
    found_by_hash = await find_existing_publication(db_session, title_hash="hash_dedup_12345")
    assert found_by_hash is not None
    assert found_by_hash.id == pub.id

    # Non-existent
    not_found = await find_existing_publication(db_session, doi="10.nonexistent/000")
    assert not_found is None


@pytest.mark.asyncio
async def test_find_existing_topic(db_session: AsyncSession):
    topic = TopicSkill(
        id=uuid.uuid4(),
        name="Reinforcement Learning",
        slug="reinforcement-learning",
        category="METHODOLOGY",
    )
    db_session.add(topic)
    await db_session.commit()

    found_by_slug = await find_existing_topic(db_session, slug="reinforcement-learning")
    assert found_by_slug is not None
    assert found_by_slug.name == "Reinforcement Learning"

    found_by_name = await find_existing_topic(db_session, name="Reinforcement Learning")
    assert found_by_name is not None
    assert found_by_name.slug == "reinforcement-learning"


@pytest.mark.asyncio
async def test_find_existing_user(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="test.dedup@university.edu",
        hashed_password="mock_password",
        role="STUDENT",
    )
    db_session.add(user)
    await db_session.commit()

    found = await find_existing_user(db_session, "TEST.DEDUP@UNIVERSITY.EDU ")
    assert found is not None
    assert found.id == user.id
