"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-22 14:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Enable pgvector extension if PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="STUDENT"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])

    # 2. students
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("student_number", sa.String(length=64), nullable=True, unique=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("department", sa.String(length=150), nullable=False),
        sa.Column("degree_level", sa.String(length=50), nullable=False, server_default="UNDERGRADUATE"),
        sa.Column("gpa_or_standing", sa.Float(), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("statement_of_purpose", sa.Text(), nullable=False),
        sa.Column("availability_status", sa.String(length=50), nullable=False, server_default="SEEKING_ADVISOR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_students_dept", "students", ["department"])
    op.create_index("idx_students_degree", "students", ["degree_level"])
    op.create_index("idx_students_availability", "students", ["availability_status"])

    # 3. faculty
    op.create_table(
        "faculty",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("faculty_number", sa.String(length=64), nullable=True, unique=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("department", sa.String(length=150), nullable=False),
        sa.Column("title_rank", sa.String(length=100), nullable=False, server_default="ASSISTANT_PROFESSOR"),
        sa.Column("office_location", sa.String(length=150), nullable=True),
        sa.Column("website_url", sa.String(length=512), nullable=True),
        sa.Column("lab_name", sa.String(length=255), nullable=True),
        sa.Column("accepting_students", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("max_capacity", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("current_student_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_faculty_dept", "faculty", ["department"])
    op.create_index("idx_faculty_accepting", "faculty", ["accepting_students"])

    # 4. topics_and_skills
    op.create_table(
        "topics_and_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False, unique=True),
        sa.Column("slug", sa.String(length=150), nullable=False, unique=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics_and_skills.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_topics_parent", "topics_and_skills", ["parent_id"])
    op.create_index("idx_topics_category", "topics_and_skills", ["category"])

    # 5. student_skills_interests
    op.create_table(
        "student_skills_interests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics_and_skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("proficiency_level", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("interest_level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("years_experience", sa.Float(), nullable=True, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("student_id", "topic_skill_id", name="uq_student_skill"),
    )
    op.create_index("idx_student_skills_student", "student_skills_interests", ["student_id"])
    op.create_index("idx_student_skills_topic", "student_skills_interests", ["topic_skill_id"])

    # 6. faculty_skills_expertise
    op.create_table(
        "faculty_skills_expertise",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics_and_skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expertise_level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_primary_focus", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("faculty_id", "topic_skill_id", name="uq_faculty_skill"),
    )
    op.create_index("idx_faculty_skills_faculty", "faculty_skills_expertise", ["faculty_id"])
    op.create_index("idx_faculty_skills_topic", "faculty_skills_expertise", ["topic_skill_id"])

    # 7. academic_projects & project_skills
    op.create_table(
        "academic_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("github_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_projects_student", "academic_projects", ["student_id"])

    op.create_table(
        "project_skills",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("topic_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics_and_skills.id", ondelete="CASCADE"), primary_key=True),
    )

    # 8. publications & publication_authorship
    op.create_table(
        "publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=False),
        sa.Column("venue", sa.String(length=255), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("doi", sa.String(length=128), nullable=True, unique=True),
        sa.Column("pmid", sa.String(length=64), nullable=True, unique=True),
        sa.Column("arxiv_id", sa.String(length=64), nullable=True, unique=True),
        sa.Column("title_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("citation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_publications_year", "publications", ["publication_year"])
    op.create_index("idx_publications_title_hash", "publications", ["title_hash"])

    op.create_table(
        "publication_authorship",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("publications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True),
        sa.Column("author_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("raw_author_name", sa.String(length=150), nullable=False),
        sa.Column("is_corresponding", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("publication_id", "faculty_id", name="uq_publication_faculty"),
    )
    op.create_index("idx_authorship_pub", "publication_authorship", ["publication_id"])
    op.create_index("idx_authorship_faculty", "publication_authorship", ["faculty_id"])

    # 9. embeddings
    if bind.dialect.name == "postgresql":
        from pgvector.sqlalchemy import Vector
        vector_type = Vector(384)
    else:
        vector_type = sa.JSON()

    op.create_table(
        "embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_type", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("vector", vector_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("entity_type", "entity_id", "embedding_type", "model_version", name="uq_entity_embedding"),
    )
    op.create_index("idx_embeddings_entity", "embeddings", ["entity_type", "entity_id"])

    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw 
            ON embeddings 
            USING hnsw (vector vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64);
            """
        )

    # 10. recommendation_runs & recommendation_results
    op.create_table(
        "recommendation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("execution_time_ms", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_rec_runs_student", "recommendation_runs", ["student_id"])

    op.create_table(
        "recommendation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("semantic_score", sa.Float(), nullable=False),
        sa.Column("skill_score", sa.Float(), nullable=False),
        sa.Column("project_score", sa.Float(), nullable=False),
        sa.Column("explanation_data", sa.JSON(), nullable=False),
        sa.Column("user_interacted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("feedback_rating", sa.Integer(), nullable=True),
        sa.Column("feedback_notes", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("run_id", "faculty_id", name="uq_run_faculty"),
    )
    op.create_index("idx_rec_results_run", "recommendation_results", ["run_id"])
    op.create_index("idx_rec_results_faculty", "recommendation_results", ["faculty_id"])

    # 11. relevance_judgments
    op.create_table(
        "relevance_judgments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False),
        sa.Column("benchmark_suite", sa.String(length=100), nullable=False, server_default="standard_eval_v1"),
        sa.Column("relevance_grade", sa.Integer(), nullable=False),
        sa.Column("annotator_id", sa.String(length=100), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("student_id", "faculty_id", "benchmark_suite", name="uq_student_faculty_suite"),
    )
    op.create_index("idx_rel_judgments_suite", "relevance_judgments", ["benchmark_suite"])

    # 12. data_sources, import_jobs, entity_provenance
    op.create_table(
        "data_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("data_source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_log", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_import_jobs_source", "import_jobs", ["data_source_id"])

    op.create_table(
        "entity_provenance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("entity_type", "entity_id", "import_job_id", name="uq_entity_provenance"),
    )
    op.create_index("idx_entity_provenance_ext", "entity_provenance", ["entity_type", "external_id"])


def downgrade() -> None:
    op.drop_table("entity_provenance")
    op.drop_table("import_jobs")
    op.drop_table("data_sources")
    op.drop_table("relevance_judgments")
    op.drop_table("recommendation_results")
    op.drop_table("recommendation_runs")
    op.drop_table("embeddings")
    op.drop_table("publication_authorship")
    op.drop_table("publications")
    op.drop_table("project_skills")
    op.drop_table("academic_projects")
    op.drop_table("faculty_skills_expertise")
    op.drop_table("student_skills_interests")
    op.drop_table("topics_and_skills")
    op.drop_table("faculty")
    op.drop_table("students")
    op.drop_table("users")
