# tests/editor/conftest.py
"""Shared fixtures for editor tests.

Uses an in-memory SQLite database with StaticPool so all connections
share the same session – identical to the pattern used in static_analysis tests.
"""

import os
import sys
import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base

# Import all models so they are registered on Base.metadata
from app.editor.models.editor import Draft, DraftVersion  # noqa: F401
from static_analysis.models.static_analysis import (  # noqa: F401
    StaticAnalysis,
    Submission,
    Assignment,
    User,
)
from authority_review.models.authority_review import AuthorityReview  # noqa: F401

# ── In-memory SQLite engine ────────────────────────────────────────────────────
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Create all tables before each test and drop them afterwards."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def db():
    """Yield a database session that is rolled back after each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def sample_assignment(db):
    """Insert a minimal Assignment row and return its ID."""
    assignment = Assignment(id=1)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@pytest.fixture()
def sample_user(db):
    """Insert a minimal User (intern) row and return its ID."""
    user = User(id=10)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def sample_submission(db):
    """Insert a minimal Submission row and return it."""
    sub = Submission(status="PENDING")
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
