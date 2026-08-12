"""add_assessment_tables

Revision ID: 20260808_0003
Revises: 20260808_0002
Create Date: 2026-08-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260808_0003'
down_revision = '20260808_0002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create assessments
    op.create_table(
        'assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('difficulty_distribution', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('topic_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_selection_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_assessments_status', 'assessments', ['status'], unique=False)

    # 2. Create question_banks
    op.create_table(
        'question_banks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='PROCESSING'),
        sa.Column('question_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parsing_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_question_banks_owner_id', 'question_banks', ['owner_id'], unique=False)

    # 3. Create questions
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('question_bank_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('constraints', sa.Text(), nullable=True),
        sa.Column('examples', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expected_time_minutes', sa.Integer(), nullable=True),
        sa.Column('programming_languages', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('starter_code', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['question_bank_id'], ['question_banks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_questions_difficulty', 'questions', ['difficulty'], unique=False)
    op.create_index('ix_questions_question_bank_id', 'questions', ['question_bank_id'], unique=False)
    op.create_index('ix_questions_topic', 'questions', ['topic'], unique=False)

    # 4. Create assessment_questions
    op.create_table(
        'assessment_questions',
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('selection_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('assessment_id', 'question_id')
    )

    # 5. Create assessment_interns
    op.create_table(
        'assessment_interns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('intern_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='ASSIGNED'),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('expired_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['intern_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assessment_id', 'intern_id', name='uq_assessment_intern')
    )
    op.create_index('ix_assessment_interns_assessment_id', 'assessment_interns', ['assessment_id'], unique=False)
    op.create_index('ix_assessment_interns_intern_id', 'assessment_interns', ['intern_id'], unique=False)

    # 6. Alter existing tables
    
    # 6a. test_cases
    op.alter_column('test_cases', 'assignment_id', existing_type=sa.INTEGER(), nullable=True)
    op.add_column('test_cases', sa.Column('question_id', sa.Integer(), nullable=True))
    op.create_index('ix_test_cases_question_id', 'test_cases', ['question_id'], unique=False)
    op.create_foreign_key('fk_test_cases_question_id', 'test_cases', 'questions', ['question_id'], ['id'], ondelete='CASCADE')

    # 6b. drafts
    op.alter_column('drafts', 'assignment_id', existing_type=sa.INTEGER(), nullable=True)
    op.add_column('drafts', sa.Column('assessment_id', sa.Integer(), nullable=True))
    op.add_column('drafts', sa.Column('question_id', sa.Integer(), nullable=True))
    op.create_index('ix_drafts_assessment_id', 'drafts', ['assessment_id'], unique=False)
    op.create_index('ix_drafts_question_id', 'drafts', ['question_id'], unique=False)
    op.create_foreign_key('fk_drafts_assessment_id', 'drafts', 'assessments', ['assessment_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_drafts_question_id', 'drafts', 'questions', ['question_id'], ['id'], ondelete='CASCADE')
    
    # Update UniqueConstraint for drafts
    op.drop_constraint('uq_draft_assignment_intern', 'drafts', type_='unique')
    op.create_unique_constraint('uq_draft_assignment_intern', 'drafts', ['assignment_id', 'assessment_id', 'question_id', 'intern_id'])

    # 6c. submission
    op.add_column('submission', sa.Column('assessment_id', sa.Integer(), nullable=True))
    op.add_column('submission', sa.Column('question_id', sa.Integer(), nullable=True))
    op.create_index('ix_submission_assessment_id', 'submission', ['assessment_id'], unique=False)
    op.create_index('ix_submission_question_id', 'submission', ['question_id'], unique=False)
    op.create_foreign_key('fk_submission_assessment_id', 'submission', 'assessments', ['assessment_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_submission_question_id', 'submission', 'questions', ['question_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # 1. Reverse changes to submission
    op.drop_constraint('fk_submission_question_id', 'submission', type_='foreignkey')
    op.drop_constraint('fk_submission_assessment_id', 'submission', type_='foreignkey')
    op.drop_index('ix_submission_question_id', table_name='submission')
    op.drop_index('ix_submission_assessment_id', table_name='submission')
    op.drop_column('submission', 'question_id')
    op.drop_column('submission', 'assessment_id')

    # 2. Reverse changes to drafts
    op.drop_constraint('uq_draft_assignment_intern', 'drafts', type_='unique')
    op.create_unique_constraint('uq_draft_assignment_intern', 'drafts', ['assignment_id', 'intern_id'])
    op.drop_constraint('fk_drafts_question_id', 'drafts', type_='foreignkey')
    op.drop_constraint('fk_drafts_assessment_id', 'drafts', type_='foreignkey')
    op.drop_index('ix_drafts_question_id', table_name='drafts')
    op.drop_index('ix_drafts_assessment_id', table_name='drafts')
    op.drop_column('drafts', 'question_id')
    op.drop_column('drafts', 'assessment_id')
    op.alter_column('drafts', 'assignment_id', existing_type=sa.INTEGER(), nullable=False)

    # 3. Reverse changes to test_cases
    op.drop_constraint('fk_test_cases_question_id', 'test_cases', type_='foreignkey')
    op.drop_index('ix_test_cases_question_id', table_name='test_cases')
    op.drop_column('test_cases', 'question_id')
    op.alter_column('test_cases', 'assignment_id', existing_type=sa.INTEGER(), nullable=False)

    # 4. Drop new tables
    op.drop_index('ix_assessment_interns_intern_id', table_name='assessment_interns')
    op.drop_index('ix_assessment_interns_assessment_id', table_name='assessment_interns')
    op.drop_table('assessment_interns')
    op.drop_table('assessment_questions')
    op.drop_index('ix_questions_topic', table_name='questions')
    op.drop_index('ix_questions_question_bank_id', table_name='questions')
    op.drop_index('ix_questions_difficulty', table_name='questions')
    op.drop_table('questions')
    op.drop_index('ix_question_banks_owner_id', table_name='question_banks')
    op.drop_table('question_banks')
    op.drop_index('ix_assessments_status', table_name='assessments')
    op.drop_table('assessments')
