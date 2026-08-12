# python_backend/app/editor/api/router.py
"""FastAPI router for the Monaco Editor backend workspace.

All routes are mounted under /api/v1/editor in main.py.

Endpoint summary
────────────────
GET  /session/{assignment_id}     → Open or resume an editor session (intern only)
GET  /template/{language}         → Retrieve a starter template
POST /draft                       → Create or autosave a draft (intern only)
GET  /draft/{draft_id}            → Get current draft state
GET  /draft/{draft_id}/versions   → Paginated version history
POST /draft/{draft_id}/reset      → Reset draft to starter template (intern only)
POST /submit                      → Make a final submission (intern only)
GET  /submission/{submission_id}  → Retrieve submission details (authority only)
"""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.editor.dependencies import get_current_user_context, get_editor_service
from app.editor.schemas.editor import (
    DraftCreateRequest,
    DraftResponse,
    DraftVersionListResponse,
    EditorSessionResponse,
    EditorSubmissionResponse,
    SubmissionRequest,
    SubmissionResponse,
    TemplateResponse,
)
from app.editor.services.editor_service import EditorService

router = APIRouter()


# ── Session ────────────────────────────────────────────────────────────────────

@router.get(
    "/session/{assignment_id}",
    response_model=EditorSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Open or resume an editor session",
    description=(
        "Returns a deterministic editor session for the authenticated intern and the "
        "specified assignment. Creates a draft (with version 1 = starter template) on "
        "first call. Subsequent calls return the existing draft unchanged."
    ),
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Intern role required"},
        404: {"description": "Assignment not found"},
    },
)
def get_editor_session(
    assignment_id: int,
    assessment_id: Optional[int] = None,
    question_id: Optional[int] = None,
    user_ctx: dict = Depends(get_current_user_context),
    service: EditorService = Depends(get_editor_service),
) -> EditorSessionResponse:
    # If assignment_id is 0, we can use assessment_id and question_id instead
    kwargs = {
        "current_user_id": user_ctx["user_id"],
        "current_user_role": user_ctx["role"],
    }
    if assignment_id != 0:
        kwargs["assignment_id"] = assignment_id
    if assessment_id:
        kwargs["assessment_id"] = assessment_id
    if question_id:
        kwargs["question_id"] = question_id
        
    return service.open_session(**kwargs)


# ── Template ───────────────────────────────────────────────────────────────────

@router.get(
    "/template/{language}",
    response_model=TemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a starter template for a given language",
    description=(
        "Returns the filename and source code of the starter template for the "
        "requested programming language.  No authentication required."
    ),
    responses={
        400: {"description": "Unsupported language"},
    },
)
def get_template(
    language: str,
    service: EditorService = Depends(get_editor_service),
) -> TemplateResponse:
    return service.get_template(language)


# ── Draft – Create / Autosave ──────────────────────────────────────────────────

@router.post(
    "/draft",
    response_model=DraftResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or autosave a draft",
    description=(
        "Upserts the intern's draft for the specified assignment and appends an "
        "immutable version record.  Safe to call on every autosave keystroke."
    ),
    responses={
        400: {"description": "Unsupported language or validation error"},
        401: {"description": "Unauthenticated"},
        403: {"description": "Draft locked after submission"},
        404: {"description": "Assignment not found"},
        413: {"description": "Code exceeds maximum allowed size"},
    },
)
def save_draft(
    payload: DraftCreateRequest,
    user_ctx: dict = Depends(get_current_user_context),
    service: EditorService = Depends(get_editor_service),
) -> DraftResponse:
    return service.save_draft(
        current_user_id=user_ctx["user_id"],
        current_user_role=user_ctx["role"],
        payload=payload,
    )


# ── Draft – Retrieve ───────────────────────────────────────────────────────────

@router.get(
    "/draft/{draft_id}",
    response_model=DraftResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current draft state",
    description=(
        "Returns the current code, language, version number, and status of a draft. "
        "Interns can only access their own drafts.  Authorities can access any submitted draft."
    ),
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Draft not found"},
    },
)
def get_draft(
    draft_id: int,
    user_ctx: dict = Depends(get_current_user_context),
    service: EditorService = Depends(get_editor_service),
) -> DraftResponse:
    return service.get_draft(
        current_user_id=user_ctx["user_id"],
        current_user_role=user_ctx["role"],
        draft_id=draft_id,
    )


# ── Draft – Version history ────────────────────────────────────────────────────

@router.get(
    "/draft/{draft_id}/versions",
    response_model=DraftVersionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List version history for a draft",
    description=(
        "Returns paginated metadata for every saved version of the draft.  "
        "Code bodies are NOT included in this list – retrieve a specific version "
        "through the draft endpoint when needed."
    ),
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Draft not found"},
    },
)
def list_draft_versions(
    draft_id: int,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    user_ctx: dict = Depends(get_current_user_context),
    service: EditorService = Depends(get_editor_service),
) -> DraftVersionListResponse:
    return service.list_draft_versions(
        current_user_id=user_ctx["user_id"],
        current_user_role=user_ctx["role"],
        draft_id=draft_id,
        page=page,
        size=size,
    )


# ── Draft – Reset ──────────────────────────────────────────────────────────────

@router.post(
    "/draft/{draft_id}/reset",
    response_model=DraftResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset a draft to the original starter template",
    description=(
        "Replaces the current draft code with the original starter template for "
        "the draft's language.  Appends a new immutable version – previous history "
        "is preserved."
    ),
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Intern role required or draft is locked"},
        404: {"description": "Draft not found"},
    },
)
def reset_draft(
    draft_id: int,
    user_ctx: dict = Depends(get_current_user_context),
    service: EditorService = Depends(get_editor_service),
) -> DraftResponse:
    return service.reset_draft(
        current_user_id=user_ctx["user_id"],
        current_user_role=user_ctx["role"],
        draft_id=draft_id,
    )


# ── Submission ─────────────────────────────────────────────────────────────────

@router.post(
    "/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Make a final submission from a draft",
    description=(
        "Creates a Submission record from the current draft code, locks the draft "
        "permanently, and triggers the downstream processing pipeline (execution "
        "engine → static analysis → AI review) asynchronously.  Returns immediately "
        "with the new submission ID."
    ),
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Intern role required or draft already locked"},
        404: {"description": "Draft not found"},
        409: {"description": "Draft has already been submitted"},
    },
)
def submit_draft(
    payload: SubmissionRequest,
    user_ctx: dict = Depends(get_current_user_context),
    service: EditorService = Depends(get_editor_service),
) -> SubmissionResponse:
    return service.submit_draft(
        current_user_id=user_ctx["user_id"],
        current_user_role=user_ctx["role"],
        draft_id=payload.draft_id,
    )


# ── Submission retrieval (authority-only) ──────────────────────────────────────

@router.get(
    "/submission/{submission_id}",
    response_model=EditorSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve submission details (authority only)",
    description=(
        "Returns the submitted source code, language, assignment, intern information, "
        "and draft metadata.  Read-only.  Authorities only."
    ),
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Authority role required"},
        404: {"description": "Submission or linked draft not found"},
    },
)
def get_submission(
    submission_id: int,
    user_ctx: dict = Depends(get_current_user_context),
    service: EditorService = Depends(get_editor_service),
) -> EditorSubmissionResponse:
    return service.get_submission(
        current_user_id=user_ctx["user_id"],
        current_user_role=user_ctx["role"],
        submission_id=submission_id,
    )
