import uuid
from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, GUID, SafeVector, TimestampMixin


class EmbeddingRecord(Base, TimestampMixin):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # STUDENT, FACULTY, PUBLICATION, PROJECT
    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), nullable=False, index=True
    )
    embedding_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # HOLISTIC_PROFILE, ABSTRACT, SKILLS_TEXT, STATEMENT
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    vector: Mapped[list] = mapped_column(SafeVector(384), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "entity_id",
            "embedding_type",
            "model_version",
            name="uq_entity_embedding",
        ),
        Index("idx_embeddings_entity", "entity_type", "entity_id"),
    )
