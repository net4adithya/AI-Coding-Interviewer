# tests/editor/test_editor_service.py
"""Unit tests for EditorService business logic."""

import os
import pytest
from unittest.mock import MagicMock

from app.editor.repositories.draft_repository import DraftRepository
from app.editor.repositories.draft_version_repository import DraftVersionRepository
from app.editor.repositories.template_repository import FileSystemTemplateRepository
from app.editor.schemas.editor import DraftCreateRequest
from app.editor.services.editor_service import EditorService
from app.editor.tasks import LoggingSubmissionProcessor
from app.editor.exceptions import (
    DraftLockedError,
    DraftAccessDeniedError,
    SubmissionAlreadyExistsError,
    CodeSizeTooLargeError,
    InternRoleRequiredError,
    AssignmentNotFoundException,
)

TEMPLATES_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "python_backend", "templates")
)


def make_service(db):
    return EditorService(
        db=db,
        draft_repo=DraftRepository(db),
        version_repo=DraftVersionRepository(db),
        template_repo=FileSystemTemplateRepository(templates_root=TEMPLATES_ROOT),
        submission_processor=LoggingSubmissionProcessor(),
    )


# ── Session ────────────────────────────────────────────────────────────────────

def test_open_session_creates_draft(db, sample_assignment, sample_user):
    svc = make_service(db)
    session = svc.open_session(
        current_user_id=sample_user.id,
        current_user_role="intern",
        assignment_id=sample_assignment.id,
    )
    assert session.assignment_id == sample_assignment.id
    assert session.draft_id is not None
    assert session.draft_version == 1
    assert session.is_locked is False


def test_open_session_idempotent(db, sample_assignment, sample_user):
    svc = make_service(db)
    s1 = svc.open_session(
        current_user_id=sample_user.id,
        current_user_role="intern",
        assignment_id=sample_assignment.id,
    )
    s2 = svc.open_session(
        current_user_id=sample_user.id,
        current_user_role="intern",
        assignment_id=sample_assignment.id,
    )
    assert s1.draft_id == s2.draft_id


def test_open_session_requires_intern(db, sample_assignment, sample_user):
    svc = make_service(db)
    with pytest.raises(InternRoleRequiredError):
        svc.open_session(
            current_user_id=sample_user.id,
            current_user_role="authority",
            assignment_id=sample_assignment.id,
        )


def test_open_session_missing_assignment(db, sample_user):
    svc = make_service(db)
    with pytest.raises(AssignmentNotFoundException):
        svc.open_session(
            current_user_id=sample_user.id,
            current_user_role="intern",
            assignment_id=9999,
        )


# ── Draft Save / Autosave ──────────────────────────────────────────────────────

def test_save_draft_creates_versions(db, sample_assignment, sample_user):
    svc = make_service(db)
    for i in range(3):
        resp = svc.save_draft(
            current_user_id=sample_user.id,
            current_user_role="intern",
            payload=DraftCreateRequest(
                assignment_id=sample_assignment.id,
                language="python",
                code=f"code version {i}",
            ),
        )
    # After 3 saves the version should be 3 (first save also creates version 1)
    assert resp.current_version == 3


def test_save_draft_code_size_limit(db, sample_assignment, sample_user, monkeypatch):
    import app.editor.services.editor_service as svc_module
    monkeypatch.setattr(svc_module, "_get_max_code_size", lambda: 10)

    svc = make_service(db)
    with pytest.raises(CodeSizeTooLargeError):
        svc.save_draft(
            current_user_id=sample_user.id,
            current_user_role="intern",
            payload=DraftCreateRequest(
                assignment_id=sample_assignment.id,
                language="python",
                code="x" * 100,
            ),
        )


def test_save_draft_locked_raises(db, sample_assignment, sample_user, sample_submission):
    svc = make_service(db)
    draft_repo = DraftRepository(db)
    draft = draft_repo.create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="",
    )
    draft_repo.lock(draft, submission_id=sample_submission.id)

    with pytest.raises(DraftLockedError):
        svc.save_draft(
            current_user_id=sample_user.id,
            current_user_role="intern",
            payload=DraftCreateRequest(
                assignment_id=sample_assignment.id,
                language="python",
                code="attempt after lock",
            ),
        )


# ── Reset ──────────────────────────────────────────────────────────────────────

def test_reset_creates_new_version(db, sample_assignment, sample_user):
    svc = make_service(db)
    # Create draft with 3 versions
    draft_resp = None
    for i in range(3):
        draft_resp = svc.save_draft(
            current_user_id=sample_user.id,
            current_user_role="intern",
            payload=DraftCreateRequest(
                assignment_id=sample_assignment.id,
                language="python",
                code=f"edit {i}",
            ),
        )
    version_before = draft_resp.current_version

    # Reset
    reset_resp = svc.reset_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        draft_id=draft_resp.id,
    )
    assert reset_resp.current_version == version_before + 1
    # Code should be the template code
    from app.editor.repositories.template_repository import FileSystemTemplateRepository
    template = FileSystemTemplateRepository(templates_root=TEMPLATES_ROOT).get_template("python")
    assert reset_resp.code == template.code


def test_reset_locked_draft_raises(db, sample_assignment, sample_user, sample_submission):
    svc = make_service(db)
    draft_repo = DraftRepository(db)
    draft = draft_repo.create(
        assignment_id=sample_assignment.id,
        intern_id=sample_user.id,
        language="python",
        code="",
    )
    draft_repo.lock(draft, submission_id=sample_submission.id)

    with pytest.raises(DraftLockedError):
        svc.reset_draft(
            current_user_id=sample_user.id,
            current_user_role="intern",
            draft_id=draft.id,
        )


# ── Submission ─────────────────────────────────────────────────────────────────

def test_submit_locks_draft(db, sample_assignment, sample_user):
    svc = make_service(db)
    draft_resp = svc.save_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        payload=DraftCreateRequest(
            assignment_id=sample_assignment.id,
            language="python",
            code="final code",
        ),
    )
    sub_resp = svc.submit_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        draft_id=draft_resp.id,
    )
    assert sub_resp.draft_locked is True
    assert sub_resp.draft_submitted is True
    assert sub_resp.submission_id is not None


def test_double_submission_rejected(db, sample_assignment, sample_user):
    svc = make_service(db)
    draft_resp = svc.save_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        payload=DraftCreateRequest(
            assignment_id=sample_assignment.id,
            language="python",
            code="code",
        ),
    )
    svc.submit_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        draft_id=draft_resp.id,
    )
    with pytest.raises((DraftLockedError, SubmissionAlreadyExistsError)):
        svc.submit_draft(
            current_user_id=sample_user.id,
            current_user_role="intern",
            draft_id=draft_resp.id,
        )
