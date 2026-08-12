# tests/execution/test_execution_api.py
"""FastAPI endpoint tests for `/api/v1/execution`."""

import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from python_backend.main import app
from app.db.base_class import Base
from app.editor.dependencies import get_db, get_current_user_context
from app.execution.dependencies import get_execution_provider
from app.execution.providers.base import BaseExecutionProvider, ExecutionRawResult
from app.editor.models.editor import Draft
from app.execution.models.test_case import TestCase
from app.execution.models.execution_result import ExecutionResult
from static_analysis.models.static_analysis import Submission, Assignment, User

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


def intern_user_context():
    return {"user_id": 10, "role": "intern"}


def authority_user_context():
    return {"user_id": 999, "role": "authority"}


mock_provider = MagicMock(spec=BaseExecutionProvider)
mock_provider.provider_name.return_value = "judge0"
mock_provider.provider_version.return_value = "v1"
mock_provider.health_check = AsyncMock(
    return_value={"provider": "judge0", "configured": True, "available": True, "version": "v1"}
)
mock_provider.execute = AsyncMock(
    return_value=ExecutionRawResult(
        token="tok-api-123",
        status_id=3,
        status_description="Accepted",
        stdout="hello\n",
        execution_time=0.05,
        memory=15000,
    )
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_and_cleanup():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_context] = intern_user_context
    app.dependency_overrides[get_execution_provider] = lambda: mock_provider

    db = TestingSessionLocal()
    db.query(ExecutionResult).delete()
    db.query(TestCase).delete()
    db.query(Draft).delete()
    db.query(Submission).delete()
    db.commit()

    if not db.query(Assignment).filter(Assignment.id == 1).first():
        db.add(Assignment(id=1))
    if not db.query(User).filter(User.id == 10).first():
        db.add(User(id=10))
    db.commit()

    sub = Submission(id=1, status="SUBMITTED")
    db.add(sub)
    db.commit()

    draft = Draft(
        id=1,
        assignment_id=1,
        intern_id=10,
        language="python",
        code="print('hello')",
        is_locked=True,
        is_submitted=True,
        submission_id=1,
    )
    db.add(draft)
    db.commit()
    db.close()

    yield

    app.dependency_overrides.clear()


def test_health_check_endpoint():
    res = client.get("/api/v1/execution/health")
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "judge0"
    assert data["configured"] is True
    assert data["available"] is True


def test_trigger_execution_endpoint_authority():
    app.dependency_overrides[get_current_user_context] = authority_user_context
    try:
        res = client.post("/api/v1/execution/submission/1")
        assert res.status_code == 202
        assert res.json()["status"] == "PROCESSING"
    finally:
        app.dependency_overrides[get_current_user_context] = intern_user_context


def test_trigger_execution_endpoint_intern_forbidden():
    res = client.post("/api/v1/execution/submission/1")
    assert res.status_code == 403


def test_get_execution_summary():
    # Pre-populate execution result
    db = TestingSessionLocal()
    tc = TestCase(assignment_id=1, expected_output="hello\n")
    db.add(tc)
    db.commit()
    db.refresh(tc)

    res_obj = ExecutionResult(
        submission_id=1,
        test_case_id=tc.id,
        provider="judge0",
        language="python",
        status="PASSED",
        passed=True,
    )
    db.add(res_obj)
    db.commit()
    db.close()

    res = client.get("/api/v1/execution/submission/1")
    assert res.status_code == 200
    data = res.json()
    assert data["submission_id"] == 1
    assert data["total_test_cases"] == 1
    assert data["pass_percentage"] == 100.0
