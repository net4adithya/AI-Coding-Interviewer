# python_backend/app/editor/schemas/editor.py
"""Pydantic request / response schemas for the editor module."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Template ──────────────────────────────────────────────────────────────────

class TemplateResponse(BaseModel):
    """A starter template for a given programming language."""

    language: str
    filename: str
    code: str

    model_config = ConfigDict(from_attributes=True)


# ── Editor Session ─────────────────────────────────────────────────────────────

class EditorSessionResponse(BaseModel):
    """Full session object returned when an intern opens an assignment in the editor."""

    session_id: str
    assignment_id: Optional[int]
    assessment_id: Optional[int] = None
    question_id: Optional[int] = None
    language: str
    template: TemplateResponse
    draft_id: int
    draft_version: int
    is_locked: bool
    is_submitted: bool

    model_config = ConfigDict(from_attributes=True)


# ── Draft Request/Response ─────────────────────────────────────────────────────

class DraftCreateRequest(BaseModel):
    """Payload for creating or autosaving a draft (upsert semantics)."""

    assignment_id: Optional[int] = Field(None, description="Target assignment ID.")
    assessment_id: Optional[int] = Field(None, description="Target assessment ID.")
    question_id: Optional[int] = Field(None, description="Target question ID.")
    language: str = Field(..., description="Programming language identifier (e.g. 'python').")
    code: str = Field(..., description="Current source code.")


class DraftUpdateRequest(BaseModel):
    """Payload for updating code in an existing draft."""

    code: str = Field(..., description="Updated source code.")


class DraftResponse(BaseModel):
    """Representation of the current state of a draft."""

    id: int
    assignment_id: Optional[int]
    assessment_id: Optional[int]
    question_id: Optional[int]
    intern_id: int
    language: str
    code: str
    current_version: int
    is_locked: bool
    is_submitted: bool
    submission_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Draft Version ──────────────────────────────────────────────────────────────

class DraftVersionResponse(BaseModel):
    """Metadata for a single historical version of a draft.

    Note: 'code' is intentionally NOT included in the list view to keep
    payloads small. Use the per-version detail endpoint to retrieve code.
    """

    id: int
    draft_id: int
    version_number: int
    language: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DraftVersionDetailResponse(DraftVersionResponse):
    """Full version response including source code (used for individual retrieval)."""

    code: str


class DraftVersionListResponse(BaseModel):
    """Paginated list of draft versions."""

    total: int
    page: int
    size: int
    items: List[DraftVersionResponse]

    model_config = ConfigDict(from_attributes=True)


# ── Submission ─────────────────────────────────────────────────────────────────

class SubmissionRequest(BaseModel):
    """Request payload to make a final submission from a draft."""

    draft_id: int = Field(..., description="The draft to submit.")


class SubmissionResponse(BaseModel):
    """Returned after a successful final submission."""

    submission_id: int
    draft_id: int
    assignment_id: Optional[int]
    assessment_id: Optional[int]
    question_id: Optional[int]
    intern_id: int
    language: str
    status: str
    draft_locked: bool
    draft_submitted: bool

    model_config = ConfigDict(from_attributes=True)


class EditorSubmissionResponse(BaseModel):
    """Authority-facing detailed submission view."""

    submission_id: int
    assignment_id: Optional[int] = None
    assessment_id: Optional[int] = None
    question_id: Optional[int] = None
    intern_id: int
    language: str
    code: str
    submitted_at: Optional[datetime]
    draft_id: int
    draft_version: int
    is_locked: bool

    model_config = ConfigDict(from_attributes=True)
