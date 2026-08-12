# tests/editor/test_draft_version_repository.py
"""Unit tests for DraftVersionRepository."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.editor.repositories.draft_repository import DraftRepository
from app.editor.repositories.draft_version_repository import DraftVersionRepository


@pytest.fixture()
def draft_repo(db):
    return DraftRepository(db)


@pytest.fixture()
def version_repo(db):
    return DraftVersionRepository(db)


@pytest.fixture()
def draft(db, draft_repo, sample_assignment, sample_user):
    return draft_repo.create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="",
    )


def test_create_version(db, version_repo, draft):
    v = version_repo.create_version(
        draft_id=draft.id, code="print('v1')", language="python"
    )
    assert v.id is not None
    assert v.version_number == 1
    assert v.code == "print('v1')"


def test_version_numbers_increment(db, version_repo, draft):
    v1 = version_repo.create_version(draft_id=draft.id, code="v1", language="python")
    v2 = version_repo.create_version(draft_id=draft.id, code="v2", language="python")
    v3 = version_repo.create_version(draft_id=draft.id, code="v3", language="python")
    assert v1.version_number == 1
    assert v2.version_number == 2
    assert v3.version_number == 3


def test_get_latest(db, version_repo, draft):
    version_repo.create_version(draft_id=draft.id, code="old", language="python")
    version_repo.create_version(draft_id=draft.id, code="new", language="python")
    latest = version_repo.get_latest(draft.id)
    assert latest.code == "new"
    assert latest.version_number == 2


def test_get_latest_version_number_no_versions(db, version_repo, draft):
    assert version_repo.get_latest_version_number(draft.id) == 0


def test_list_versions_paginated(db, version_repo, draft):
    for i in range(5):
        version_repo.create_version(draft_id=draft.id, code=f"v{i}", language="python")

    total, page1 = version_repo.list_versions(draft.id, page=1, size=3)
    assert total == 5
    assert len(page1) == 3

    total2, page2 = version_repo.list_versions(draft.id, page=2, size=3)
    assert total2 == 5
    assert len(page2) == 2


def test_duplicate_version_number_rejected(db, version_repo, draft):
    """The DB uniqueness constraint must prevent duplicate version numbers."""
    from app.editor.models.editor import DraftVersion
    from datetime import datetime

    v1 = DraftVersion(draft_id=draft.id, version_number=1, code="a", language="python", created_at=datetime.utcnow())
    db.add(v1)
    db.commit()

    v2 = DraftVersion(draft_id=draft.id, version_number=1, code="b", language="python", created_at=datetime.utcnow())
    db.add(v2)
    with pytest.raises(IntegrityError):
        db.commit()
