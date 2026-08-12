# tests/editor/test_editor_permissions.py
"""Permission enforcement tests for the editor module."""

import os
import pytest

from app.editor.repositories.draft_repository import DraftRepository
from app.editor.repositories.draft_version_repository import DraftVersionRepository
from app.editor.repositories.template_repository import FileSystemTemplateRepository
from app.editor.schemas.editor import DraftCreateRequest
from app.editor.services.editor_service import EditorService
from app.editor.tasks import LoggingSubmissionProcessor
from app.editor.exceptions import (
    DraftAccessDeniedError,
    InternRoleRequiredError,
    AuthorityRoleRequiredError,
)
from static_analysis.models.static_analysis import User

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


@pytest.fixture()
def second_user(db):
    user = User(id=99)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_draft(svc, user_id, assignment_id):
    return svc.save_draft(
        current_user_id=user_id,
        current_user_role="intern",
        payload=DraftCreateRequest(
            assignment_id=assignment_id,
            language="python",
            code="intern code",
        ),
    )


# ── Intern cannot access another intern's draft ────────────────────────────────

def test_intern_cannot_get_other_draft(db, sample_assignment, sample_user, second_user):
    svc = make_service(db)
    draft_resp = _create_draft(svc, sample_user.id, sample_assignment.id)

    with pytest.raises(DraftAccessDeniedError):
        svc.get_draft(
            current_user_id=second_user.id,
            current_user_role="intern",
            draft_id=draft_resp.id,
        )


def test_intern_cannot_reset_other_draft(db, sample_assignment, sample_user, second_user):
    svc = make_service(db)
    draft_resp = _create_draft(svc, sample_user.id, sample_assignment.id)

    with pytest.raises(DraftAccessDeniedError):
        svc.reset_draft(
            current_user_id=second_user.id,
            current_user_role="intern",
            draft_id=draft_resp.id,
        )


def test_intern_cannot_submit_other_draft(db, sample_assignment, sample_user, second_user):
    svc = make_service(db)
    draft_resp = _create_draft(svc, sample_user.id, sample_assignment.id)

    with pytest.raises(DraftAccessDeniedError):
        svc.submit_draft(
            current_user_id=second_user.id,
            current_user_role="intern",
            draft_id=draft_resp.id,
        )


# ── Authority can read submitted drafts ───────────────────────────────────────

def test_authority_can_read_submitted_draft(db, sample_assignment, sample_user):
    svc = make_service(db)
    draft_resp = _create_draft(svc, sample_user.id, sample_assignment.id)
    svc.submit_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        draft_id=draft_resp.id,
    )

    # Authority reads the draft
    result = svc.get_draft(
        current_user_id=999,  # Different user – authority
        current_user_role="authority",
        draft_id=draft_resp.id,
    )
    assert result.id == draft_resp.id
    assert result.is_locked is True


# ── Authority cannot modify drafts ─────────────────────────────────────────────

def test_authority_cannot_save_draft(db, sample_assignment, sample_user):
    svc = make_service(db)
    with pytest.raises(InternRoleRequiredError):
        svc.save_draft(
            current_user_id=999,
            current_user_role="authority",
            payload=DraftCreateRequest(
                assignment_id=sample_assignment.id,
                language="python",
                code="bad",
            ),
        )


def test_authority_cannot_reset_draft(db, sample_assignment, sample_user):
    svc = make_service(db)
    draft_resp = _create_draft(svc, sample_user.id, sample_assignment.id)

    with pytest.raises(InternRoleRequiredError):
        svc.reset_draft(
            current_user_id=999,
            current_user_role="authority",
            draft_id=draft_resp.id,
        )


def test_authority_cannot_submit_draft(db, sample_assignment, sample_user):
    svc = make_service(db)
    draft_resp = _create_draft(svc, sample_user.id, sample_assignment.id)

    with pytest.raises(InternRoleRequiredError):
        svc.submit_draft(
            current_user_id=999,
            current_user_role="authority",
            draft_id=draft_resp.id,
        )


# ── Intern cannot access authority submission endpoint ─────────────────────────

def test_intern_cannot_get_submission(db, sample_assignment, sample_user):
    svc = make_service(db)
    draft_resp = _create_draft(svc, sample_user.id, sample_assignment.id)
    sub_resp = svc.submit_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        draft_id=draft_resp.id,
    )

    with pytest.raises(AuthorityRoleRequiredError):
        svc.get_submission(
            current_user_id=sample_user.id,
            current_user_role="intern",
            submission_id=sub_resp.submission_id,
        )
