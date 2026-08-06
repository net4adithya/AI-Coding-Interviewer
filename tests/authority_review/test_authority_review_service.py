import pytest
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from authority_review.models.authority_review import AuthorityReview, ReviewStatusEnum, ReviewDecisionEnum
from authority_review.repositories.authority_review_repository import AuthorityReviewRepository
from authority_review.services.authority_review_service import AuthorityReviewService
from authority_review.utils.event_publisher import InMemoryEventPublisher

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    # Create submission table stub for status cascade
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS submission (id INTEGER PRIMARY KEY, status TEXT)"))
        conn.execute(text("INSERT INTO submission (id, status) VALUES (601, 'PENDING')"))
        conn.commit()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_service_get_or_create_auto_under_review(db_session):
    repo = AuthorityReviewRepository(db_session)
    event_pub = InMemoryEventPublisher()
    service = AuthorityReviewService(db_session, repo, event_pub)

    # First call: creates UNDER_REVIEW record automatically
    aggregated = service.get_aggregated_review(submission_id=601, reviewer_id=10)
    assert aggregated.authority_review.submission_id == 601
    assert aggregated.authority_review.status == "UNDER_REVIEW"
    assert aggregated.docker_execution.is_placeholder is True

    # Second call: retrieves existing record without duplicates
    aggregated2 = service.get_aggregated_review(submission_id=601, reviewer_id=10)
    assert aggregated2.authority_review.id == aggregated.authority_review.id

def test_service_approve_decision_and_event_publishing(db_session):
    repo = AuthorityReviewRepository(db_session)
    event_pub = InMemoryEventPublisher()
    service = AuthorityReviewService(db_session, repo, event_pub)

    res = service.approve_submission(submission_id=601, reviewer_id=5, internal_notes="Looks great!")
    assert res.status == "APPROVED"
    assert res.decision == "APPROVE"
    assert res.internal_notes == "Looks great!"

    # Check notification event published
    assert len(event_pub.published_events) == 1
    assert event_pub.published_events[0]["event_name"] == "submission_approved"

def test_service_reject_and_resubmit(db_session):
    repo = AuthorityReviewRepository(db_session)
    event_pub = InMemoryEventPublisher()
    service = AuthorityReviewService(db_session, repo, event_pub)

    rej = service.reject_submission(submission_id=601, reviewer_id=5, internal_notes="Fails requirements")
    assert rej.status == "REJECTED"
    assert event_pub.published_events[-1]["event_name"] == "submission_rejected"

    resub = service.request_resubmission(submission_id=601, reviewer_id=5, internal_notes="Please refactor")
    assert resub.status == "RESUBMISSION_REQUESTED"
    assert event_pub.published_events[-1]["event_name"] == "submission_resubmission_requested"

def test_service_internal_notes(db_session):
    repo = AuthorityReviewRepository(db_session)
    event_pub = InMemoryEventPublisher()
    service = AuthorityReviewService(db_session, repo, event_pub)

    res = service.add_internal_notes(submission_id=601, reviewer_id=5, internal_notes="Confidential note")
    assert res.internal_notes == "Confidential note"
