"""Tests for the EmbeddingService: text hashing, deterministic projection,
batch encoding, get_or_create caching, and sync_all_embeddings.
"""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.embeddings.service import EmbeddingService
from backend.app.models.embedding import EmbeddingRecord
from backend.app.models.faculty import Faculty
from backend.app.models.project import AcademicProject
from backend.app.models.publication import Publication
from backend.app.models.student import Student
from backend.app.models.user import User


class TestEmbeddingServiceUnit:
    """Pure unit tests that do not require a database."""

    def test_embed_text_returns_vector(self):
        svc = EmbeddingService(
            model_name="test-model",
            dimension=64,
        )
        vec = svc.embed_text("Machine learning and deep neural networks")
        assert vec is not None
        assert len(vec) == 64
        assert all(isinstance(v, float) for v in vec)

    def test_embed_text_returns_none_for_empty(self):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        assert svc.embed_text("") is None
        assert svc.embed_text(None) is None
        assert svc.embed_text("   ") is None

    def test_embed_text_is_normalized(self):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        vec = svc.embed_text("Normalization test with enough words for a valid embedding")
        if vec:
            import numpy as np
            norm = float(np.linalg.norm(vec))
            assert abs(norm - 1.0) < 0.01, f"Vector should be unit normalized, got norm={norm}"

    def test_embed_text_deterministic(self):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        text = "Reproducible deterministic embedding vector for testing"
        vec1 = svc.embed_text(text)
        vec2 = svc.embed_text(text)
        assert vec1 == vec2, "Same text should produce identical vectors"

    def test_embed_text_different_texts_differ(self):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        v1 = svc.embed_text("Natural language processing and transformer models")
        v2 = svc.embed_text("Quantum computing and superconducting circuits")
        assert v1 != v2, "Different texts should produce different vectors"

    def test_embed_batch(self):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        texts = [
            "Deep learning for computer vision",
            "",
            "Natural language understanding",
            None,
        ]
        results = svc.embed_batch(texts)
        assert len(results) == 4
        assert results[0] is not None
        assert results[1] is None  # empty
        assert results[2] is not None
        assert results[3] is None  # None

    def test_text_hash_consistency(self):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        h1 = svc._hash_text("test string")
        h2 = svc._hash_text("test string")
        h3 = svc._hash_text("different string")
        assert h1 == h2
        assert h1 != h3


class TestEmbeddingServiceDB:
    """Integration tests requiring a database session."""

    @pytest.mark.asyncio
    async def test_get_or_create_embedding(self, db_session: AsyncSession):
        svc = EmbeddingService(model_name="test-model", dimension=64)

        entity_id = uuid.uuid4()
        rec = await svc.get_or_create_embedding(
            db_session,
            entity_type="STUDENT",
            entity_id=entity_id,
            embedding_type="STATEMENT",
            source_text="My research interests lie in artificial intelligence and machine learning.",
        )
        assert rec is not None
        assert rec.entity_type == "STUDENT"
        assert rec.entity_id == entity_id
        assert rec.embedding_type == "STATEMENT"
        assert len(rec.vector) == 64

    @pytest.mark.asyncio
    async def test_get_or_create_idempotent(self, db_session: AsyncSession):
        svc = EmbeddingService(model_name="test-model", dimension=64)

        entity_id = uuid.uuid4()
        text = "Computer vision and deep learning applications"
        rec1 = await svc.get_or_create_embedding(
            db_session, "FACULTY", entity_id, "HOLISTIC_PROFILE", text
        )
        rec2 = await svc.get_or_create_embedding(
            db_session, "FACULTY", entity_id, "HOLISTIC_PROFILE", text
        )
        assert rec1.id == rec2.id, "Should return same record on repeat call"
        count = (
            await db_session.execute(
                select(EmbeddingRecord).where(
                    EmbeddingRecord.entity_id == entity_id,
                    EmbeddingRecord.embedding_type == "HOLISTIC_PROFILE",
                )
            )
        ).scalars().all()
        assert len(count) == 1

    @pytest.mark.asyncio
    async def test_get_or_create_reuses_existing_embedding(self, db_session: AsyncSession):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        entity_id = uuid.uuid4()
        existing = EmbeddingRecord(
            id=uuid.uuid4(),
            entity_type="PROJECT",
            entity_id=entity_id,
            embedding_type="STATEMENT",
            model_name="test-model",
            model_version=svc.model_version,
            vector=svc.embed_text("Existing project embedding is reused safely"),
        )
        db_session.add(existing)
        await db_session.commit()

        result = await svc.get_or_create_embedding(
            db_session,
            "PROJECT",
            entity_id,
            "STATEMENT",
            "Existing project embedding is reused safely",
        )

        assert result is not None
        assert result.id == existing.id
        count = (
            await db_session.execute(
                select(EmbeddingRecord).where(
                    EmbeddingRecord.entity_type == "PROJECT",
                    EmbeddingRecord.entity_id == entity_id,
                    EmbeddingRecord.embedding_type == "STATEMENT",
                    EmbeddingRecord.model_version == svc.model_version,
                )
            )
        ).scalars().all()
        assert len(count) == 1

    @pytest.mark.asyncio
    async def test_force_refresh_updates_an_already_loaded_embedding(
        self, db_session: AsyncSession
    ):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        entity_id = uuid.uuid4()
        original_text = "Original research embedding text for refresh validation"
        refreshed_text = "A different research focus requiring a fresh vector representation"
        existing = await svc.get_or_create_embedding(
            db_session, "PUBLICATION", entity_id, "ABSTRACT", original_text
        )
        original_vector = list(existing.vector)

        refreshed = await svc.get_or_create_embedding(
            db_session,
            "PUBLICATION",
            entity_id,
            "ABSTRACT",
            refreshed_text,
            force_refresh=True,
        )

        assert refreshed.id == existing.id
        assert list(refreshed.vector) == svc.embed_text(refreshed_text)
        assert list(refreshed.vector) != original_vector

    @pytest.mark.asyncio
    async def test_get_or_create_returns_none_for_empty(self, db_session: AsyncSession):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        rec = await svc.get_or_create_embedding(
            db_session, "STUDENT", uuid.uuid4(), "STATEMENT", ""
        )
        assert rec is None

    @pytest.mark.asyncio
    async def test_sync_all_embeddings(
        self, db_session: AsyncSession, monkeypatch
    ):
        svc = EmbeddingService(model_name="test-model", dimension=64)
        embed_batch = svc.embed_batch
        batch_sizes = []

        def capture_batch_size(texts):
            batch_sizes.append(len(texts))
            return embed_batch(texts)

        monkeypatch.setattr(svc, "embed_batch", capture_batch_size)

        # Create minimal entities
        user1 = User(
            id=uuid.uuid4(),
            email="embed_student@test.edu",
            hashed_password="test",
            role="STUDENT",
            is_active=True,
        )
        db_session.add(user1)
        await db_session.flush()

        student = Student(
            id=uuid.uuid4(),
            user_id=user1.id,
            first_name="Test",
            last_name="Student",
            department="Computer Science",
            degree_level="PHD",
            statement_of_purpose="I want to study reinforcement learning for robotic control.",
        )
        db_session.add(student)

        user2 = User(
            id=uuid.uuid4(),
            email="embed_faculty@test.edu",
            hashed_password="test",
            role="FACULTY",
            is_active=True,
        )
        db_session.add(user2)
        await db_session.flush()

        faculty = Faculty(
            id=uuid.uuid4(),
            user_id=user2.id,
            first_name="Dr",
            last_name="Smith",
            department="Computer Science",
            title_rank="ASSOCIATE_PROFESSOR",
            bio="Research in reinforcement learning and control theory.",
            lab_name="Autonomous Systems Lab",
        )
        db_session.add(faculty)

        pub = Publication(
            id=uuid.uuid4(),
            title="Deep Reinforcement Learning for Robot Navigation",
            abstract="We present a novel approach to autonomous navigation using deep RL.",
            venue="IROS 2024",
            publication_year=2024,
            title_hash="test_pub_hash_" + uuid.uuid4().hex[:8],
        )
        db_session.add(pub)

        project = AcademicProject(
            id=uuid.uuid4(),
            student_id=student.id,
            title="RL-Based Path Planning",
            description="Implemented A3C algorithm for robot path planning.",
        )
        db_session.add(project)

        await db_session.commit()

        # Run sync
        stats = await svc.sync_all_embeddings(db_session)
        assert batch_sizes == [4]

        assert stats["students_embedded"] >= 1
        assert stats["faculty_embedded"] >= 1
        assert stats["publications_embedded"] >= 1
        assert stats["projects_embedded"] >= 1

        # Verify embeddings exist in DB
        emb_count = (
            await db_session.execute(
                select(EmbeddingRecord)
            )
        ).scalars().all()
        assert len(emb_count) >= 4

        stats_again = await svc.sync_all_embeddings(db_session)
        assert stats_again == stats
        assert batch_sizes == [4]
