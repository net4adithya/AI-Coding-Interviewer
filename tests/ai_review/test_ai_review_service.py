import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from app.db.base_class import Base
from ai_review.models.ai_review import AIReview, ReviewStatusEnum
from ai_review.services.ai_review_service import AIReviewService
from ai_review.providers.mock_provider import MockAIProvider

# In-memory SQLite database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

class MockSubmission:
    def __init__(self, sub_id: int):
        self.id = sub_id
        self.code = "def solution(arr): return sorted(arr)"
        self.language = "python"
        self.assignment_id = 10
        self.intern_id = 5

def test_service_generate_and_save_review(db):
    service = AIReviewService(db=db, provider=MockAIProvider())
    submission = MockSubmission(sub_id=200)

    review = service.generate_and_save_review(submission, prompt_version="v1")
    assert review is not None
    assert review.submission_id == 200
    assert review.review_status == ReviewStatusEnum.COMPLETED
    assert review.overall_score == 85.0
    assert review.correctness_score == 85.0
    assert review.recommendation == "PASS"

def test_service_health_check(db):
    service = AIReviewService(db=db, provider=MockAIProvider())
    health = service.health_check()
    assert health["available"] is True
    assert health["provider"] == "MockAI"
