# python_backend/app/editor/repositories/draft_repository.py
"""Repository for Draft CRUD operations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.editor.models.editor import Draft


class DraftRepository:
    """Database operations for Draft records."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, draft_id: int) -> Optional[Draft]:
        """Return a Draft by primary key, or None."""
        return self.db.query(Draft).filter(Draft.id == draft_id).first()

    def get_unique_draft(
        self,
        intern_id: int,
        assignment_id: Optional[int] = None,
        assessment_id: Optional[int] = None,
        question_id: Optional[int] = None,
    ) -> Optional[Draft]:
        """Return the single draft for a given identifier pair."""
        query = self.db.query(Draft).filter(Draft.intern_id == intern_id)
        if assignment_id:
            query = query.filter(Draft.assignment_id == assignment_id)
        if assessment_id and question_id:
            query = query.filter(
                Draft.assessment_id == assessment_id,
                Draft.question_id == question_id
            )
        return query.first()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        intern_id: int,
        language: str,
        code: str,
        assignment_id: Optional[int] = None,
        assessment_id: Optional[int] = None,
        question_id: Optional[int] = None,
    ) -> Draft:
        """Insert a new Draft and return the persisted object."""
        draft = Draft(
            assignment_id=assignment_id,
            assessment_id=assessment_id,
            question_id=question_id,
            intern_id=intern_id,
            language=language.lower(),
            code=code,
            is_locked=False,
            is_submitted=False,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def update_code(self, draft: Draft, *, code: str, language: Optional[str] = None) -> Draft:
        """Update the code (and optionally the language) of a draft."""
        draft.code = code
        if language is not None:
            draft.language = language.lower()
        draft.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def lock(self, draft: Draft, *, submission_id: int) -> Draft:
        """Mark a draft as locked and submitted, and link to the submission."""
        draft.is_locked = True
        draft.is_submitted = True
        draft.submission_id = submission_id
        draft.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(draft)
        return draft

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_or_create(
        self,
        *,
        intern_id: int,
        language: str,
        code: str,
        assignment_id: Optional[int] = None,
        assessment_id: Optional[int] = None,
        question_id: Optional[int] = None,
    ) -> tuple[Draft, bool]:
        """Return (draft, created) where *created* is True if a new row was inserted."""
        existing = self.get_unique_draft(
            intern_id=intern_id,
            assignment_id=assignment_id,
            assessment_id=assessment_id,
            question_id=question_id
        )
        if existing:
            return existing, False
        created = self.create(
            assignment_id=assignment_id,
            assessment_id=assessment_id,
            question_id=question_id,
            intern_id=intern_id,
            language=language,
            code=code,
        )
        return created, True
