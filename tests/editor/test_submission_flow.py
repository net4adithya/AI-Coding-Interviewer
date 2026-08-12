# tests/editor/test_submission_flow.py
"""Tests for the final submission flow including locking and processing trigger."""

import os
import pytest
from unittest.mock import MagicMock, call

from app.editor.repositories.draft_repository import DraftRepository
from app.editor.repositories.draft_version_repository import DraftVersionRepository
from app.editor.repositories.template_repository import FileSystemTemplateRepository
from app.editor.schemas.editor import DraftCreateRequest
from app.editor.services.editor_service import EditorService
from app.editor.tasks import SubmissionProcessingInterface, LoggingSubmissionProcessor
from app.editor.exceptions import DraftLockedError, SubmissionAlreadyExistsError

TEMPLATES_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "python_backend", "templates")
)


def make_service(db, processor=None):
    return EditorService(
        db=db,
        draft_repo=DraftRepository(db),
        version_repo=DraftVersionRepository(db),
        template_repo=FileSystemTemplateRepository(templates_root=TEMPLATES_ROOT),
        submission_processor=processor or LoggingSubmissionProcessor(),
    )


def test_submission_creates_record_and_locks(db, sample_assignment, sample_user):
    mock_processor = MagicMock(spec=SubmissionProcessingInterface)
    svc = make_service(db, processor=mock_processor)

    draft_resp = svc.save_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        payload=DraftCreateRequest(
            assignment_id=sample_assignment.id,
            language="python",
            code="my solution",
        ),
    )
    sub_resp = svc.submit_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        draft_id=draft_resp.id,
    )

    assert sub_resp.submission_id is not None
    assert sub_resp.draft_locked is True
    assert sub_resp.draft_submitted is True
    assert sub_resp.language == "python"
    assert sub_resp.assignment_id == sample_assignment.id
    assert sub_resp.intern_id == sample_user.id

    # Processing task must have been triggered exactly once
    mock_processor.trigger.assert_called_once_with(sub_resp.submission_id)


def test_locked_draft_cannot_be_updated(db, sample_assignment, sample_user):
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


def test_locked_draft_cannot_be_reset(db, sample_assignment, sample_user):
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

    with pytest.raises(DraftLockedError):
        svc.reset_draft(
            current_user_id=sample_user.id,
            current_user_role="intern",
            draft_id=draft_resp.id,
        )


def test_authority_can_retrieve_submission(db, sample_assignment, sample_user):
    svc = make_service(db)
    draft_resp = svc.save_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        payload=DraftCreateRequest(
            assignment_id=sample_assignment.id,
            language="python",
            code="my solution",
        ),
    )
    sub_resp = svc.submit_draft(
        current_user_id=sample_user.id,
        current_user_role="intern",
        draft_id=draft_resp.id,
    )

    detail = svc.get_submission(
        current_user_id=999,
        current_user_role="authority",
        submission_id=sub_resp.submission_id,
    )
    assert detail.submission_id == sub_resp.submission_id
    assert detail.code == "my solution"
    assert detail.is_locked is True
