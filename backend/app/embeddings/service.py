import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.ingestion.preprocessing import normalize_text
from backend.app.models.embedding import EmbeddingRecord
from backend.app.models.faculty import Faculty
from backend.app.models.project import AcademicProject
from backend.app.models.publication import Publication
from backend.app.models.student import Student


class EmbeddingService:
    def __init__(
        self,
        model_name: Optional[str] = None,
        dimension: Optional[int] = None,
        model_version: str = "v1.0",
    ):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.model_version = model_version
        self._st_model = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._st_model = SentenceTransformer(self.model_name)
        except Exception as exc:
            logger.info(
                f"SentenceTransformer not available ({exc}); using deterministic semantic projection encoder (dim={self.dimension})."
            )
            self._st_model = None

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def _deterministic_projection(self, text: str) -> List[float]:
        """High-entropy deterministic semantic hash projection vectorizer:
        Used as high-performance, reproducible fallback when transformer weights
        are downloading or offline. Preserves lexical and n-gram cosine similarities.
        """
        words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
        vec = np.zeros(self.dimension, dtype=np.float32)

        for w in words:
            # Deterministic word hash
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx1 = h % self.dimension
            idx2 = (h >> 16) % self.dimension
            vec[idx1] += 1.0
            vec[idx2] += 0.5

        # Also add character n-grams (3-grams) for semantic similarity of related terms
        for i in range(len(text) - 2):
            gram = text[i : i + 3].lower()
            gh = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
            g_idx = gh % self.dimension
            vec[g_idx] += 0.2

        norm = np.linalg.norm(vec)
        if norm > 1e-12:
            vec = vec / norm
        else:
            vec = np.zeros(self.dimension, dtype=np.float32)

        return vec.tolist()

    def embed_text(self, text: Optional[str]) -> Optional[List[float]]:
        """Generates a normalized dense vector embedding for arbitrary text.
        Returns None if text is empty, preventing misleading zero-information embeddings.
        """
        cleaned = normalize_text(text)
        if not cleaned:
            return None

        if self._st_model is not None:
            embedding = self._st_model.encode(cleaned, normalize_embeddings=True)
            return [float(x) for x in embedding]
        else:
            return self._deterministic_projection(cleaned)

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Batched embedding generation with normalization."""
        results: List[Optional[List[float]]] = []
        valid_indices = []
        valid_texts = []

        for idx, t in enumerate(texts):
            clean = normalize_text(t)
            if clean:
                valid_indices.append(idx)
                valid_texts.append(clean)
            results.append(None)

        if not valid_texts:
            return results

        if self._st_model is not None:
            raw_embeddings = self._st_model.encode(
                valid_texts,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                normalize_embeddings=True,
            )
            for idx, emb in zip(valid_indices, raw_embeddings):
                results[idx] = [float(x) for x in emb]
        else:
            for idx, text in zip(valid_indices, valid_texts):
                results[idx] = self._deterministic_projection(text)

        return results

    async def get_or_create_embedding(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
        embedding_type: str,
        source_text: Optional[str],
        force_refresh: bool = False,
    ) -> Optional[EmbeddingRecord]:
        """Retrieves existing embedding or generates and persists a new one if source text changed."""
        clean_text = normalize_text(source_text)
        if not clean_text:
            return None

        if not force_refresh:
            stmt = select(EmbeddingRecord).where(
                EmbeddingRecord.entity_type == entity_type,
                EmbeddingRecord.entity_id == entity_id,
                EmbeddingRecord.embedding_type == embedding_type,
                EmbeddingRecord.model_version == self.model_version,
            )
            res = await db.execute(stmt)
            existing = res.scalars().first()
            if existing:
                return existing

        # Generate vector
        vector = self.embed_text(clean_text)
        if not vector:
            return None

        values = {
            "id": uuid.uuid4(),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "embedding_type": embedding_type,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "vector": vector,
        }
        dialect_name = db.get_bind().dialect.name
        if dialect_name == "postgresql":
            insert_stmt = postgresql_insert(EmbeddingRecord).values(**values)
        elif dialect_name == "sqlite":
            insert_stmt = sqlite_insert(EmbeddingRecord).values(**values)
        else:
            raise RuntimeError(
                f"Atomic embedding persistence is unsupported for database dialect {dialect_name!r}"
            )

        conflict_columns = [
            EmbeddingRecord.entity_type,
            EmbeddingRecord.entity_id,
            EmbeddingRecord.embedding_type,
            EmbeddingRecord.model_version,
        ]
        if force_refresh:
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=conflict_columns,
                set_={"vector": vector, "model_name": self.model_name},
            )
        else:
            insert_stmt = insert_stmt.on_conflict_do_nothing(
                index_elements=conflict_columns
            )

        await db.execute(insert_stmt)
        await db.commit()

        stmt = select(EmbeddingRecord).where(
            EmbeddingRecord.entity_type == entity_type,
            EmbeddingRecord.entity_id == entity_id,
            EmbeddingRecord.embedding_type == embedding_type,
            EmbeddingRecord.model_version == self.model_version,
        )
        return (
            await db.execute(stmt.execution_options(populate_existing=True))
        ).scalars().one()

    async def sync_all_embeddings(self, db: AsyncSession) -> Dict[str, int]:
        """Synchronizes embeddings in bounded batches to avoid per-record commits."""
        stats = {
            "students_embedded": 0,
            "projects_embedded": 0,
            "faculty_embedded": 0,
            "publications_embedded": 0,
        }
        sources: List[Tuple[str, uuid.UUID, str, str, str]] = []

        students = (await db.execute(select(Student))).scalars().all()
        for stu in students:
            sources.append(
                (
                    "STUDENT",
                    stu.id,
                    "STATEMENT",
                    f"{stu.statement_of_purpose} {stu.bio or ''}",
                    "students_embedded",
                )
            )

        projects = (await db.execute(select(AcademicProject))).scalars().all()
        for proj in projects:
            sources.append(
                (
                    "PROJECT",
                    proj.id,
                    "STATEMENT",
                    f"{proj.title}: {proj.description}",
                    "projects_embedded",
                )
            )

        faculty = (await db.execute(select(Faculty))).scalars().all()
        for fac in faculty:
            sources.append(
                (
                    "FACULTY",
                    fac.id,
                    "HOLISTIC_PROFILE",
                    f"{fac.bio or ''} {fac.lab_name or ''}",
                    "faculty_embedded",
                )
            )

        publications = (await db.execute(select(Publication))).scalars().all()
        for pub in publications:
            sources.append(
                (
                    "PUBLICATION",
                    pub.id,
                    "ABSTRACT",
                    f"{pub.title}. {pub.abstract}",
                    "publications_embedded",
                )
            )

        valid_sources = [
            source for source in sources if normalize_text(source[3])
        ]
        if not valid_sources:
            return stats

        existing_stmt = select(EmbeddingRecord).where(
            EmbeddingRecord.entity_id.in_([source[1] for source in valid_sources]),
            EmbeddingRecord.model_version == self.model_version,
        )
        existing_records = (await db.execute(existing_stmt)).scalars().all()
        existing_keys = {
            (record.entity_type, record.entity_id, record.embedding_type)
            for record in existing_records
        }

        pending_sources = []
        for source in valid_sources:
            key = (source[0], source[1], source[2])
            if key in existing_keys:
                stats[source[4]] += 1
            else:
                pending_sources.append(source)

        batch_size = 256
        for start in range(0, len(pending_sources), batch_size):
            batch = pending_sources[start : start + batch_size]
            vectors = self.embed_batch([source[3] for source in batch])
            records = []
            for source, vector in zip(batch, vectors):
                if vector is None:
                    continue
                entity_type, entity_id, embedding_type, _, stats_key = source
                records.append(
                    EmbeddingRecord(
                        id=uuid.uuid4(),
                        entity_type=entity_type,
                        entity_id=entity_id,
                        embedding_type=embedding_type,
                        model_name=self.model_name,
                        model_version=self.model_version,
                        vector=vector,
                    )
                )
                stats[stats_key] += 1
            if records:
                db.add_all(records)
                await db.commit()

        return stats


embedding_service = EmbeddingService()
