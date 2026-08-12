"""add_users_and_decisions

Revision ID: 20260809_0004
Revises: 20260808_0003
Create Date: 2026-08-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260809_0004'
down_revision = '20260808_0003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('supabase_uid', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='intern'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('supabase_uid', name='uq_users_supabase_uid'),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    op.create_index('ix_users_supabase_uid', 'users', ['supabase_uid'], unique=True)

    # 2. Create authority_decisions
    op.create_table(
        'authority_decisions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('assessment_intern_id', sa.Integer(), nullable=False),
        sa.Column('decision', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['assessment_intern_id'], ['assessment_interns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assessment_intern_id', name='uq_authority_decisions_assessment_intern_id')
    )
    op.create_index('ix_authority_decisions_assessment_intern_id', 'authority_decisions', ['assessment_intern_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_authority_decisions_assessment_intern_id', table_name='authority_decisions')
    op.drop_table('authority_decisions')
    op.drop_index('ix_users_supabase_uid', table_name='users')
    op.drop_table('users')
