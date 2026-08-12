# tests/execution/conftest.py
"""Shared fixtures for execution engine tests."""

import os
import sys
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.editor.models.editor import Draft, DraftVersion  # noqa: F401
from app.execution.models.test_case import TestCase  # noqa: F401
from app.execution.models.execution_result import ExecutionResult  # noqa: F401
from static_analysis.models.static_analysis import Submission, Assignment, User, StaticAnalysis  # noqa: F401
from authority_review.models.authority_review import AuthorityReview  # noqa: F401

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def sample_assignment(db):
    assignment = Assignment(id=1)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@pytest.fixture()
def sample_user(db):
    user = User(id=10)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def sample_submission(db, sample_assignment, sample_user):
    sub = Submission(id=1, status="SUBMITTED")
    db.add(sub)
    db.commit()
    db.refresh(sub)

    draft = Draft(
        id=1,
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="print('hello')",
        is_locked=True,
        is_submitted=True,
        submission_id=sub.id,
    )
    db.add(draft)
    db.commit()
    return sub
