"""002_real_data_provenance

Revision ID: 002_real_data_provenance
Revises: 001_initial_schema
Create Date: 2026-10-22 23:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_real_data_provenance"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Faculty additions
    op.add_column(
        "faculty",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "faculty",
        sa.Column(
            "verification_status",
            sa.String(length=50),
            nullable=False,
            server_default="VERIFIED",
        ),
    )
    op.add_column(
        "faculty",
        sa.Column("openalex_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "faculty",
        sa.Column("institution_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "faculty",
        sa.Column("institution_ror", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "faculty",
        sa.Column("verification_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "faculty",
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("faculty", "user_id", nullable=True)

    op.create_index("idx_faculty_synthetic", "faculty", ["is_synthetic"])
    op.create_index("idx_faculty_verification", "faculty", ["verification_status"])
    op.create_index("idx_faculty_openalex", "faculty", ["openalex_id"])

    # 2. Publications additions
    op.add_column(
        "publications",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "publications",
        sa.Column("openalex_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "publications",
        sa.Column("crossref_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "publications",
        sa.Column(
            "is_retracted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.create_index("idx_publications_synthetic", "publications", ["is_synthetic"])
    op.create_index("idx_publications_openalex", "publications", ["openalex_id"])

    # 3. Students additions
    op.add_column(
        "students",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.create_index("idx_students_synthetic", "students", ["is_synthetic"])


def downgrade() -> None:
    op.drop_index("idx_students_synthetic", table_name="students")
    op.drop_column("students", "is_synthetic")

    op.drop_index("idx_publications_openalex", table_name="publications")
    op.drop_index("idx_publications_synthetic", table_name="publications")
    op.drop_column("publications", "is_retracted")
    op.drop_column("publications", "crossref_id")
    op.drop_column("publications", "openalex_id")
    op.drop_column("publications", "is_synthetic")

    op.drop_index("idx_faculty_openalex", table_name="faculty")
    op.drop_index("idx_faculty_verification", table_name="faculty")
    op.drop_index("idx_faculty_synthetic", table_name="faculty")
    op.alter_column("faculty", "user_id", nullable=False)
    op.drop_column("faculty", "verified_at")
    op.drop_column("faculty", "verification_notes")
    op.drop_column("faculty", "institution_ror")
    op.drop_column("faculty", "institution_name")
    op.drop_column("faculty", "openalex_id")
    op.drop_column("faculty", "verification_status")
    op.drop_column("faculty", "is_synthetic")
