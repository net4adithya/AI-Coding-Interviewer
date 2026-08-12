# tests/editor/test_draft_repository.py
"""Unit tests for DraftRepository."""

import pytest
from app.editor.repositories.draft_repository import DraftRepository


@pytest.fixture()
def draft_repo(db):
    return DraftRepository(db)


def test_create_draft(db, draft_repo, sample_assignment, sample_user):
    draft = draft_repo.create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="print('hello')",
    )
    assert draft.id is not None
    assert draft.assignment_id == sample_assignment.id
    assert draft.intern_id == sample_user.id
    assert draft.language == "python"
    assert draft.is_locked is False
    assert draft.is_submitted is False


def test_get_by_id(db, draft_repo, sample_assignment, sample_user):
    draft = draft_repo.create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="x = 1",
    )
    fetched = draft_repo.get_by_id(draft.id)
    assert fetched is not None
    assert fetched.id == draft.id


def test_get_by_id_missing(draft_repo):
    assert draft_repo.get_by_id(99999) is None


def test_get_by_assignment_and_intern(db, draft_repo, sample_assignment, sample_user):
    draft_repo.create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="",
    )
    found = draft_repo.get_by_assignment_and_intern(sample_assignment.id, sample_user.id)
    assert found is not None


def test_update_code(db, draft_repo, sample_assignment, sample_user):
    draft = draft_repo.create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="original",
    )
    updated = draft_repo.update_code(draft, code="new code")
    assert updated.code == "new code"


def test_lock_draft(db, draft_repo, sample_assignment, sample_user, sample_submission):
    draft = draft_repo.create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="final code",
    )
    locked = draft_repo.lock(draft, submission_id=sample_submission.id)
    assert locked.is_locked is True
    assert locked.is_submitted is True
    assert locked.submission_id == sample_submission.id


def test_get_or_create_returns_existing(db, draft_repo, sample_assignment, sample_user):
    d1, created1 = draft_repo.get_or_create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="",
    )
    d2, created2 = draft_repo.get_or_create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="new",
    )
    assert created1 is True
    assert created2 is False
    assert d1.id == d2.id


def test_uniqueness_constraint(db, draft_repo, sample_assignment, sample_user):
    """Two creates for the same (assignment, intern) must fail at the DB level."""
    from sqlalchemy.exc import IntegrityError
    draft_repo.create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="",
    )
    with pytest.raises(IntegrityError):
        draft_repo.create(
            assignment_id=sample_assignment.id,
            intern_id=sample_user.id,
            language="python",
            code="duplicate",
        )
