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
from static_analysis.api.router import get_db

# Use StaticPool so all connections share the same SQLite in-memory database
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

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_api_create_static_analysis():
    payload = {
        "submission_id": 301,
        "assignment_id": 10,
        "intern_id": 20,
        "language": "python",
        "source_code": "def hello():\n    print('world')\n"
    }
    response = client.post("/static-analysis/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["submission_id"] == 301
    assert data["language"] == "python"
    assert "request_id" in data
    assert data["analysis_status"] == "COMPLETED"

def test_api_create_duplicate_conflict():
    payload = {
        "submission_id": 302,
        "language": "java",
        "source_code": "public class App {}"
    }
    res1 = client.post("/static-analysis/", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/static-analysis/", json=payload)
    assert res2.status_code == 409

def test_api_get_by_id_and_list():
    payload = {
        "submission_id": 303,
        "language": "go",
        "source_code": "package main\nfunc main() {}\n"
    }
    res = client.post("/static-analysis/", json=payload)
    created_id = res.json()["id"]

    # Get by ID
    get_res = client.get(f"/static-analysis/{created_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == created_id

    # List with pagination
    list_res = client.get("/static-analysis/?page=1&size=20&language=go")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == created_id for item in list_data["items"])

def test_api_delete_soft_delete():
    payload = {
        "submission_id": 304,
        "language": "rust",
        "source_code": "fn main() {}\n"
    }
    res = client.post("/static-analysis/", json=payload)
    created_id = res.json()["id"]

    del_res = client.delete(f"/static-analysis/{created_id}")
    assert del_res.status_code == 204

    # GET should return 404 after soft delete
    get_after = client.get(f"/static-analysis/{created_id}")
    assert get_after.status_code == 404
