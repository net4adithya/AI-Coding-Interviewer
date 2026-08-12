# tests/editor/test_editor_api.py
"""FastAPI HTTP-level tests for the editor router.

Uses the same TestClient + in-memory SQLite override pattern as the
static_analysis API tests.
"""

import os
import sys
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from python_backend.main import app
from app.db.base_class import Base
from app.editor.dependencies import get_db, get_current_user_context, get_submission_processor
from app.editor.tasks import SubmissionProcessingInterface
from static_analysis.models.static_analysis import Assignment, User

# Import models to register metadata
from app.editor.models.editor import Draft, DraftVersion  # noqa: F401
from static_analysis.models.static_analysis import Submission, StaticAnalysis  # noqa: F401
from authority_review.models.authority_review import AuthorityReview  # noqa: F401

# ── In-memory SQLite for tests ─────────────────────────────────────────────────
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


INTERN_USER_ID = 10
AUTHORITY_USER_ID = 20

# Mock user contexts
def intern_user_context():
    return {"user_id": INTERN_USER_ID, "role": "intern"}


def authority_user_context():
    return {"user_id": AUTHORITY_USER_ID, "role": "authority"}


mock_processor = MagicMock(spec=SubmissionProcessingInterface)


def override_processor():
    return mock_processor


client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_and_cleanup():
    """Seed required rows and clean up between tests."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_context] = intern_user_context
    app.dependency_overrides[get_submission_processor] = override_processor

    db = TestingSessionLocal()
    # Insert assignment and user
    if not db.query(Assignment).filter(Assignment.id == 1).first():
        db.add(Assignment(id=1))
    if not db.query(User).filter(User.id == INTERN_USER_ID).first():
        db.add(User(id=INTERN_USER_ID))
    if not db.query(User).filter(User.id == AUTHORITY_USER_ID).first():
        db.add(User(id=AUTHORITY_USER_ID))
    db.commit()
    db.close()

    yield

    # Cleanup drafts and versions between tests
    db = TestingSessionLocal()
    db.query(DraftVersion).delete()
    db.query(Draft).delete()
    db.query(Submission).delete()
    db.commit()
    db.close()
    mock_processor.reset_mock()
    app.dependency_overrides.clear()


# ── Template ────────────────────────────────────────────────────────────────────

def test_get_template_python():
    res = client.get("/api/v1/editor/template/python")
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "python"
    assert "starter.py" in data["filename"]
    assert len(data["code"]) > 0


def test_get_template_unsupported():
    res = client.get("/api/v1/editor/template/brainfuck")
    assert res.status_code == 400


# ── Draft ────────────────────────────────────────────────────────────────────────

def test_save_draft():
    payload = {"assignment_id": 1, "language": "python", "code": "print('hello')"}
    res = client.post("/api/v1/editor/draft", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "python"
    assert data["current_version"] >= 1
    assert data["is_locked"] is False


def test_get_draft():
    payload = {"assignment_id": 1, "language": "python", "code": "x=1"}
    save_res = client.post("/api/v1/editor/draft", json=payload)
    draft_id = save_res.json()["id"]

    res = client.get(f"/api/v1/editor/draft/{draft_id}")
    assert res.status_code == 200
    assert res.json()["id"] == draft_id


def test_get_draft_not_found():
    res = client.get("/api/v1/editor/draft/99999")
    assert res.status_code == 404


def test_list_versions():
    payload = {"assignment_id": 1, "language": "python", "code": "v1"}
    save_res = client.post("/api/v1/editor/draft", json=payload)
    draft_id = save_res.json()["id"]
    # Save a few more versions
    client.post("/api/v1/editor/draft", json={**payload, "code": "v2"})
    client.post("/api/v1/editor/draft", json={**payload, "code": "v3"})

    res = client.get(f"/api/v1/editor/draft/{draft_id}/versions")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 3


def test_reset_draft():
    payload = {"assignment_id": 1, "language": "python", "code": "edit 1"}
    save_res = client.post("/api/v1/editor/draft", json=payload)
    draft_id = save_res.json()["id"]
    version_before = save_res.json()["current_version"]

    res = client.post(f"/api/v1/editor/draft/{draft_id}/reset")
    assert res.status_code == 200
    data = res.json()
    assert data["current_version"] == version_before + 1


# ── Submission ────────────────────────────────────────────────────────────────────

def test_submit_draft():
    payload = {"assignment_id": 1, "language": "python", "code": "final"}
    save_res = client.post("/api/v1/editor/draft", json=payload)
    draft_id = save_res.json()["id"]

    sub_res = client.post("/api/v1/editor/submit", json={"draft_id": draft_id})
    assert sub_res.status_code == 201
    sub_data = sub_res.json()
    assert sub_data["draft_locked"] is True
    assert sub_data["submission_id"] is not None
    assert mock_processor.trigger.called


def test_submit_then_save_rejected():
    payload = {"assignment_id": 1, "language": "python", "code": "final"}
    save_res = client.post("/api/v1/editor/draft", json=payload)
    draft_id = save_res.json()["id"]
    client.post("/api/v1/editor/submit", json={"draft_id": draft_id})

    # Attempt autosave after submission
    retry = client.post("/api/v1/editor/draft", json=payload)
    assert retry.status_code == 403


def test_double_submit_rejected():
    payload = {"assignment_id": 1, "language": "python", "code": "final"}
    save_res = client.post("/api/v1/editor/draft", json=payload)
    draft_id = save_res.json()["id"]

    client.post("/api/v1/editor/submit", json={"draft_id": draft_id})
    retry = client.post("/api/v1/editor/submit", json={"draft_id": draft_id})
    assert retry.status_code in (403, 409)


# ── Authority endpoint ─────────────────────────────────────────────────────────

def test_authority_gets_submission():
    # Override context to intern for creating the draft
    payload = {"assignment_id": 1, "language": "python", "code": "my code"}
    save_res = client.post("/api/v1/editor/draft", json=payload)
    draft_id = save_res.json()["id"]
    sub_res = client.post("/api/v1/editor/submit", json={"draft_id": draft_id})
    sub_id = sub_res.json()["submission_id"]

    # Switch to authority context
    app.dependency_overrides[get_current_user_context] = authority_user_context
    try:
        res = client.get(f"/api/v1/editor/submission/{sub_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["is_locked"] is True
        assert data["code"] == "my code"
    finally:
        app.dependency_overrides[get_current_user_context] = intern_user_context
