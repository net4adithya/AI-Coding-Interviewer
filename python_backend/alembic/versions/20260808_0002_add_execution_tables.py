"""add_execution_tables

Revision ID: 20260808_0002
Revises: 20260808_0001
Create Date: 2026-08-08

Creates:
  - test_cases
  - execution_results
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "20260808_0002"
down_revision = "20260808_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── test_cases ─────────────────────────────────────────────────────────────
    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignment.id"), nullable=False),
        sa.Column("stdin", sa.Text(), nullable=False, server_default=""),
        sa.Column("expected_output", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("time_limit_sec", sa.Float(), nullable=False, server_default="10.0"),
        sa.Column("memory_limit_mb", sa.Integer(), nullable=False, server_default="512"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_test_cases_assignment_id", "test_cases", ["assignment_id"])
    op.create_index("ix_test_cases_is_hidden", "test_cases", ["is_hidden"])
    op.create_index("ix_test_cases_assignment_hidden", "test_cases", ["assignment_id", "is_hidden"])

    # ── execution_results ──────────────────────────────────────────────────────
    op.create_table(
        "execution_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submission.id"), nullable=False),
        sa.Column("test_case_id", sa.Integer(), sa.ForeignKey("test_cases.id"), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="judge0"),
        sa.Column("language", sa.String(length=64), nullable=False),
        sa.Column("judge0_token", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="PENDING"),
        sa.Column("status_id", sa.Integer(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("compile_output", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("execution_time", sa.Float(), nullable=True),
        sa.Column("memory", sa.Integer(), nullable=True),
        sa.Column("expected_output", sa.Text(), nullable=True),
        sa.Column("actual_output", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("submission_id", "test_case_id", name="uq_submission_test_case_result"),
    )

    op.create_index("ix_execution_results_submission_id", "execution_results", ["submission_id"])
    op.create_index("ix_execution_results_test_case_id", "execution_results", ["test_case_id"])
    op.create_index("ix_execution_results_status", "execution_results", ["status"])
    op.create_index("ix_execution_results_created_at", "execution_results", ["created_at"])
    op.create_index("ix_execution_results_submission_status", "execution_results", ["submission_id", "status"])


def downgrade() -> None:
    op.drop_table("execution_results")
    op.drop_table("test_cases")
