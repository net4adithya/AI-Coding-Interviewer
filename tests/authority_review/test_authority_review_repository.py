import pytest
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from authority_review.models.authority_review import AuthorityReview, ReviewStatusEnum, ReviewDecisionEnum
from authority_review.repositories.authority_review_repository import AuthorityReviewRepository

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_repository_crud_operations(db_session):
    repo = AuthorityReviewRepository(db_session)
    review = AuthorityReview(
        request_id="req-12345",
        submission_id=501,
        assignment_id=10,
        intern_id=20,
        status=ReviewStatusEnum.UNDER_REVIEW,
    )
    created = repo.create(review)
    assert created.id is not None
    assert created.submission_id == 501
    assert created.status == ReviewStatusEnum.UNDER_REVIEW

    # Get by submission ID
    fetched = repo.get_by_submission_id(501)
    assert fetched is not None
    assert fetched.id == created.id

    # Update decision
    fetched.status = ReviewStatusEnum.APPROVED
    fetched.decision = ReviewDecisionEnum.APPROVE
    updated = repo.update(fetched)
    assert updated.status == ReviewStatusEnum.APPROVED

    # Soft delete
    deleted = repo.soft_delete(created.id)
    assert deleted is True
    assert repo.get_by_id(created.id) is None
    assert repo.get_by_submission_id(501) is None

def test_repository_list_filtering(db_session):
    repo = AuthorityReviewRepository(db_session)
    repo.create(AuthorityReview(request_id="r1", submission_id=1, status=ReviewStatusEnum.APPROVED))
    repo.create(AuthorityReview(request_id="r2", submission_id=2, status=ReviewStatusEnum.REJECTED))

    total, items = repo.list(filters={"status": ReviewStatusEnum.APPROVED})
    assert total == 1
    assert items[0].submission_id == 1
