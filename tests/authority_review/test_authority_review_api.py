import pytest
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from python_backend.main import app
from app.db.base_class import Base
from authority_review.api.router import get_db

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)
headers = {"X-User-Role": "AUTHORITY", "X-User-Id": "1"}

def test_api_get_authority_review_auto_creates():
    res = client.get("/authority-review/801", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["submission"]["submission_id"] == 801
    assert data["authority_review"]["status"] == "UNDER_REVIEW"
    assert data["docker_execution"]["is_placeholder"] is True

def test_api_approve_submission():
    payload = {"internal_notes": "Code clean and well structured."}
    res = client.post("/authority-review/801/approve", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "APPROVED"
    assert data["decision"] == "APPROVE"
    assert data["internal_notes"] == "Code clean and well structured."

def test_api_reject_submission():
    payload = {"internal_notes": "Fails basic formatting guidelines."}
    res = client.post("/authority-review/802/reject", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REJECTED"
    assert data["decision"] == "REJECT"

def test_api_resubmit_submission():
    payload = {"internal_notes": "Please address static analysis complexity warnings."}
    res = client.post("/authority-review/803/resubmit", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RESUBMISSION_REQUESTED"
    assert data["decision"] == "RESUBMIT"

def test_api_save_internal_notes():
    payload = {"internal_notes": "Notes updated separately."}
    res = client.post("/authority-review/801/notes", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["internal_notes"] == "Notes updated separately."

def test_api_list_authority_reviews():
    res = client.get("/authority-review/?page=1&size=20", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3
