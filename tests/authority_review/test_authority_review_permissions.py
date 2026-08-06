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

def test_intern_access_blocked_with_403():
    # Intern role header
    headers = {"X-User-Role": "INTERN", "X-User-Id": "99"}

    # Attempt GET aggregated review
    response = client.get("/authority-review/701", headers=headers)
    assert response.status_code == 403
    assert "Interns are not authorized" in response.json()["detail"]

    # Attempt Approve
    approve_res = client.post("/authority-review/701/approve", headers=headers)
    assert approve_res.status_code == 403

def test_authority_access_permitted():
    headers = {"X-User-Role": "AUTHORITY", "X-User-Id": "1"}
    response = client.get("/authority-review/702", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["authority_review"]["submission_id"] == 702
