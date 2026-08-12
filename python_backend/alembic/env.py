"""Alembic env.py – database migration environment."""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Make both python_backend and root importable
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
sys.path.insert(0, backend_dir)
sys.path.insert(0, root_dir)

from app.config import settings
from app.db.base_class import Base

# Import all models so their metadata is registered
from app.editor.models.editor import Draft, DraftVersion  # noqa: F401
from static_analysis.models.static_analysis import StaticAnalysis, Submission, Assignment  # noqa: F401
from authority_review.models.authority_review import AuthorityReview  # noqa: F401
from app.assessment.models.assessment import QuestionBank, Question, Assessment, AssessmentQuestion, AssessmentIntern, AuthorityDecision # noqa: F401
from app.users.models import User # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_url = settings.DATABASE_URL.replace("%", "%%").replace("?schema=public&", "?").replace("?schema=public", "")
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
