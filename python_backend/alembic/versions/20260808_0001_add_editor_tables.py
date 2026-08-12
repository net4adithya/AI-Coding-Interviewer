"""add_editor_tables

Revision ID: 20260808_0001
Revises: 
Create Date: 2026-08-08

Creates:
  - drafts
  - draft_versions
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "20260808_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── drafts ────────────────────────────────────────────────────────────────
    op.create_table(
        "drafts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignment.id"), nullable=False),
        sa.Column("intern_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=False),
        sa.Column("code", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_submitted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submission.id"), nullable=True),
        sa.UniqueConstraint("assignment_id", "intern_id", name="uq_draft_assignment_intern"),
    )

    op.create_index("ix_drafts_assignment_id", "drafts", ["assignment_id"])
    op.create_index("ix_drafts_intern_id", "drafts", ["intern_id"])
    op.create_index("ix_drafts_updated_at", "drafts", ["updated_at"])
    op.create_index("ix_drafts_is_locked", "drafts", ["is_locked"])

    # ── draft_versions ────────────────────────────────────────────────────────
    op.create_table(
        "draft_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "draft_id",
            sa.Integer(),
            sa.ForeignKey("drafts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False, server_default=""),
        sa.Column("language", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("draft_id", "version_number", name="uq_draft_version_number"),
    )


def downgrade() -> None:
    op.drop_table("draft_versions")
    op.drop_table("drafts")
