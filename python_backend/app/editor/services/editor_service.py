# python_backend/app/editor/services/editor_service.py
"""Core business logic for the editor module.

This service orchestrates:
  - Editor session creation / retrieval
  - Draft upsert with immutable version history
  - Draft reset to starter template
  - Final submission creation and draft locking
  - Audit event logging
  - Background task triggering

It does NOT calculate scores, execute code, or call Gemini directly.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.editor.exceptions import (
    AssignmentNotFoundException,
    AuthorityRoleRequiredError,
    CodeSizeTooLargeError,
    DraftAccessDeniedError,
    DraftLockedError,
    DraftNotFoundException,
    InternRoleRequiredError,
    SubmissionAlreadyExistsError,
)
from app.editor.interfaces.template_repository import Template, TemplateRepositoryInterface
from app.editor.models.editor import Draft, DraftVersion
from app.editor.repositories.draft_repository import DraftRepository
from app.editor.repositories.draft_version_repository import DraftVersionRepository
from app.editor.schemas.editor import (
    DraftCreateRequest,
    DraftResponse,
    DraftVersionListResponse,
    DraftVersionResponse,
    EditorSessionResponse,
    EditorSubmissionResponse,
    SubmissionResponse,
    TemplateResponse,
)
from app.editor.tasks import SubmissionProcessingInterface
from static_analysis.models.static_analysis import Submission, Assignment
from app.users.models import User

logger = logging.getLogger(__name__)

# Default code size limit: 100 KB.  Override via EDITOR_MAX_CODE_SIZE env var.
_DEFAULT_MAX_CODE_SIZE = 100 * 1024  # bytes


def _get_max_code_size() -> int:
    try:
        return int(getattr(settings, "EDITOR_MAX_CODE_SIZE", _DEFAULT_MAX_CODE_SIZE))
    except (TypeError, ValueError):
        return _DEFAULT_MAX_CODE_SIZE


def _audit(event: str, **kwargs) -> None:
    """Lightweight structured audit log.

    Intentionally does NOT log source code contents.
    """
    safe_kwargs = {k: v for k, v in kwargs.items() if k != "code"}
    logger.info("[AUDIT] event=%s %s", event, safe_kwargs)


def _draft_to_response(draft: Draft, current_version: int) -> DraftResponse:
    return DraftResponse(
        id=draft.id,
        assignment_id=draft.assignment_id,
        assessment_id=draft.assessment_id,
        question_id=draft.question_id,
        intern_id=draft.intern_id,
        language=draft.language,
        code=draft.code,
        current_version=current_version,
        is_locked=draft.is_locked,
        is_submitted=draft.is_submitted,
        submission_id=draft.submission_id,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


class EditorService:
    """Business logic for the Monaco Editor backend workspace."""

    def __init__(
        self,
        db: Session,
        draft_repo: DraftRepository,
        version_repo: DraftVersionRepository,
        template_repo: TemplateRepositoryInterface,
        submission_processor: SubmissionProcessingInterface,
    ):
        self.db = db
        self.draft_repo = draft_repo
        self.version_repo = version_repo
        self.template_repo = template_repo
        self.submission_processor = submission_processor

    # ──────────────────────────────────────────────────────────────────────────
    # Session
    # ──────────────────────────────────────────────────────────────────────────

    def open_session(
        self,
        *,
        current_user_id: int,
        current_user_role: str,
        assignment_id: Optional[int] = None,
        assessment_id: Optional[int] = None,
        question_id: Optional[int] = None,
    ) -> EditorSessionResponse:
        """Open (or resume) an editor session for an intern on an assignment.

        Returns a deterministic session object – repeated calls do NOT create
        duplicate drafts.
        """
        if current_user_role.lower() not in ("intern",):
            raise InternRoleRequiredError()

        if not assignment_id and not (assessment_id and question_id):
            raise ValueError("Must provide either assignment_id or both assessment_id and question_id")

        if assignment_id:
            # Verify the assignment exists
            assignment = self.db.query(Assignment).filter(Assignment.id == assignment_id).first()
            if not assignment:
                raise AssignmentNotFoundException(assignment_id)

        # Determine language (default to Python for now; a real implementation
        # would read the assignment's configured language).
        language = "python"
        
        # Load starter template (from Question if assessment, otherwise generic)
        starter_code = None
        if assessment_id and question_id:
            from app.assessment.models.assessment import Question
            question = self.db.query(Question).filter(Question.id == question_id).first()
            if question and question.starter_code and language in question.starter_code:
                starter_code = question.starter_code[language]

        template = self.template_repo.get_template(language)
        if starter_code is None:
            starter_code = template.code

        # Get or create draft (idempotent)
        draft, created = self.draft_repo.get_or_create(
            assignment_id=assignment_id,
            assessment_id=assessment_id,
            question_id=question_id,
            intern_id=current_user_id,
            language=language,
            code=starter_code,
        )

        # If newly created, record version 1 (starter template)
        if created:
            self.version_repo.create_version(
                draft_id=draft.id,
                code=template.code,
                language=language,
            )
            _audit(
                "draft_created",
                user_id=current_user_id,
                assignment_id=assignment_id,
                draft_id=draft.id,
            )
        else:
            _audit(
                "editor_session_opened",
                user_id=current_user_id,
                assignment_id=assignment_id,
                draft_id=draft.id,
            )

        current_version = self.version_repo.get_latest_version_number(draft.id)

        return EditorSessionResponse(
            session_id=str(uuid.uuid4()),
            assignment_id=assignment_id,
            assessment_id=assessment_id,
            question_id=question_id,
            language=language,
            template=TemplateResponse(
                language=template.language,
                filename=template.filename,
                code=template.code,
            ),
            draft_id=draft.id,
            draft_version=current_version,
            is_locked=draft.is_locked,
            is_submitted=draft.is_submitted,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Template
    # ──────────────────────────────────────────────────────────────────────────

    def get_template(self, language: str) -> TemplateResponse:
        """Return a starter template for the requested language."""
        template = self.template_repo.get_template(language)
        return TemplateResponse(
            language=template.language,
            filename=template.filename,
            code=template.code,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Draft – Save (create / autosave / upsert)
    # ──────────────────────────────────────────────────────────────────────────

    def save_draft(
        self,
        *,
        current_user_id: int,
        current_user_role: str,
        payload: DraftCreateRequest,
    ) -> DraftResponse:
        """Upsert a draft and append an immutable version record.

        Safe for autosave: repeated calls always increment the version.
        Rejects payloads that exceed EDITOR_MAX_CODE_SIZE.
        """
        if current_user_role.lower() not in ("intern",):
            raise InternRoleRequiredError()

        self._check_code_size(payload.code)

        if payload.assignment_id:
            # Verify assignment
            assignment = self.db.query(Assignment).filter(Assignment.id == payload.assignment_id).first()
            if not assignment:
                raise AssignmentNotFoundException(payload.assignment_id)

        draft, created = self.draft_repo.get_or_create(
            assignment_id=payload.assignment_id,
            assessment_id=payload.assessment_id,
            question_id=payload.question_id,
            intern_id=current_user_id,
            language=payload.language,
            code=payload.code,
        )

        if draft.is_locked:
            raise DraftLockedError(draft.id)

        if not created:
            # Existing draft – update code
            self.draft_repo.update_code(draft, code=payload.code, language=payload.language)

        # Always create a new immutable version snapshot
        version = self.version_repo.create_version(
            draft_id=draft.id,
            code=payload.code,
            language=payload.language,
        )

        event = "draft_created" if created else "draft_updated"
        _audit(event, user_id=current_user_id, assignment_id=payload.assignment_id, draft_id=draft.id)

        return _draft_to_response(draft, version.version_number)

    # ──────────────────────────────────────────────────────────────────────────
    # Draft – Retrieve
    # ──────────────────────────────────────────────────────────────────────────

    def get_draft(
        self,
        *,
        current_user_id: int,
        current_user_role: str,
        draft_id: int,
    ) -> DraftResponse:
        """Return the current state of a draft.

        Interns can only see their own drafts.
        Authorities can see any submitted draft (read-only).
        """
        draft = self._get_draft_or_404(draft_id)
        self._assert_read_access(draft, current_user_id, current_user_role)

        current_version = self.version_repo.get_latest_version_number(draft.id)
        return _draft_to_response(draft, current_version)

    # ──────────────────────────────────────────────────────────────────────────
    # Draft – Version history
    # ──────────────────────────────────────────────────────────────────────────

    def list_draft_versions(
        self,
        *,
        current_user_id: int,
        current_user_role: str,
        draft_id: int,
        page: int = 1,
        size: int = 20,
    ) -> DraftVersionListResponse:
        """Return paginated version history metadata (no code bodies)."""
        draft = self._get_draft_or_404(draft_id)
        self._assert_read_access(draft, current_user_id, current_user_role)

        total, items = self.version_repo.list_versions(draft_id, page=page, size=size)
        return DraftVersionListResponse(
            total=total,
            page=page,
            size=size,
            items=[
                DraftVersionResponse(
                    id=v.id,
                    draft_id=v.draft_id,
                    version_number=v.version_number,
                    language=v.language,
                    created_at=v.created_at,
                )
                for v in items
            ],
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Draft – Reset
    # ──────────────────────────────────────────────────────────────────────────

    def reset_draft(
        self,
        *,
        current_user_id: int,
        current_user_role: str,
        draft_id: int,
    ) -> DraftResponse:
        """Reset the draft code to the original starter template.

        Existing version history is preserved; a new version is appended.
        """
        if current_user_role.lower() not in ("intern",):
            raise InternRoleRequiredError()

        draft = self._get_draft_or_404(draft_id)
        self._assert_intern_ownership(draft, current_user_id)

        if draft.is_locked:
            raise DraftLockedError(draft_id)

        # Load starter template
        starter_code = None
        if draft.assessment_id and draft.question_id:
            from app.assessment.models.assessment import Question
            question = self.db.query(Question).filter(Question.id == draft.question_id).first()
            if question and question.starter_code and draft.language in question.starter_code:
                starter_code = question.starter_code[draft.language]
                
        template = self.template_repo.get_template(draft.language)
        if starter_code is None:
            starter_code = template.code

        # Replace current code with template
        self.draft_repo.update_code(draft, code=starter_code, language=draft.language)

        # Append new version (history intact)
        version = self.version_repo.create_version(
            draft_id=draft.id,
            code=starter_code,
            language=draft.language,
        )

        _audit(
            "draft_reset",
            user_id=current_user_id,
            assignment_id=draft.assignment_id,
            draft_id=draft.id,
            new_version=version.version_number,
        )

        return _draft_to_response(draft, version.version_number)

    # ──────────────────────────────────────────────────────────────────────────
    # Submission
    # ──────────────────────────────────────────────────────────────────────────

    def submit_draft(
        self,
        *,
        current_user_id: int,
        current_user_role: str,
        draft_id: int,
    ) -> SubmissionResponse:
        """Make a final submission from a draft.

        1. Validates ownership and state.
        2. Creates a Submission record (existing model).
        3. Locks the draft.
        4. Triggers background processing (non-blocking).
        5. Emits audit events.
        """
        if current_user_role.lower() not in ("intern",):
            raise InternRoleRequiredError()

        draft = self._get_draft_or_404(draft_id)
        self._assert_intern_ownership(draft, current_user_id)

        if draft.is_locked:
            raise DraftLockedError(draft_id)

        if draft.is_submitted:
            raise SubmissionAlreadyExistsError(draft_id)

        # Create a Submission record using the existing model
        submission = Submission(status="PENDING", assessment_id=draft.assessment_id, question_id=draft.question_id)
        self.db.add(submission)
        self.db.flush()  # Get the generated ID before committing

        # Lock the draft and link it to the new submission
        self.draft_repo.lock(draft, submission_id=submission.id)

        self.db.commit()
        self.db.refresh(submission)
        self.db.refresh(draft)

        current_version = self.version_repo.get_latest_version_number(draft.id)

        _audit(
            "submission_created",
            user_id=current_user_id,
            assignment_id=draft.assignment_id,
            draft_id=draft.id,
            submission_id=submission.id,
        )
        _audit(
            "draft_locked",
            user_id=current_user_id,
            draft_id=draft.id,
            submission_id=submission.id,
        )

        # Trigger the processing pipeline (non-blocking, Phase 8 connects here)
        self.submission_processor.trigger(submission.id)

        return SubmissionResponse(
            submission_id=submission.id,
            draft_id=draft.id,
            assignment_id=draft.assignment_id,
            assessment_id=draft.assessment_id,
            question_id=draft.question_id,
            intern_id=draft.intern_id,
            language=draft.language,
            status=submission.status,
            draft_locked=draft.is_locked,
            draft_submitted=draft.is_submitted,
        )

    def get_submission(
        self,
        *,
        current_user_id: int,
        current_user_role: str,
        submission_id: int,
    ) -> EditorSubmissionResponse:
        """Return detailed submission info.  Authority-only endpoint."""
        if current_user_role.lower() not in ("authority", "admin"):
            raise AuthorityRoleRequiredError()

        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission {submission_id} not found.",
            )

        # Find the associated draft
        draft = (
            self.db.query(Draft)
            .filter(Draft.submission_id == submission_id)
            .first()
        )
        if not draft:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No draft linked to submission {submission_id}.",
            )

        current_version = self.version_repo.get_latest_version_number(draft.id)

        return EditorSubmissionResponse(
            submission_id=submission.id,
            assignment_id=draft.assignment_id,
            intern_id=draft.intern_id,
            language=draft.language,
            code=draft.code,
            submitted_at=draft.updated_at,
            draft_id=draft.id,
            draft_version=current_version,
            is_locked=draft.is_locked,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _check_code_size(self, code: str) -> None:
        max_size = _get_max_code_size()
        byte_size = len(code.encode("utf-8"))
        if byte_size > max_size:
            raise CodeSizeTooLargeError(byte_size, max_size)

    def _get_draft_or_404(self, draft_id: int) -> Draft:
        draft = self.draft_repo.get_by_id(draft_id)
        if not draft:
            raise DraftNotFoundException(draft_id)
        return draft

    def _assert_intern_ownership(self, draft: Draft, current_user_id: int) -> None:
        if draft.intern_id != current_user_id:
            raise DraftAccessDeniedError()

    def _assert_read_access(self, draft: Draft, current_user_id: int, role: str) -> None:
        role_lower = role.lower()
        if role_lower in ("authority", "admin"):
            return  # authorities have read-only access to any draft
        if role_lower == "intern":
            if draft.intern_id != current_user_id:
                raise DraftAccessDeniedError()
            return
        raise DraftAccessDeniedError()
