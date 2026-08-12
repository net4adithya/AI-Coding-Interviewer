# python_backend/app/editor/models/editor.py
"""SQLAlchemy models for the editor module: Draft and DraftVersion."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Draft(Base):
    """Represents an intern's in-progress coding workspace for an assignment.

    One draft exists per (assignment_id, intern_id) combination.
    Once submitted, the draft is locked (is_locked=True) and immutable.
    """

    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignment.id"), nullable=True) # Modified to be nullable for assessments
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    intern_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String(64), nullable=False)
    code = Column(Text, nullable=False, default="")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    is_locked = Column(Boolean, default=False, nullable=False)
    is_submitted = Column(Boolean, default=False, nullable=False)

    # Nullable FK – set after final submission to link to the created Submission record
    submission_id = Column(
        Integer, ForeignKey("submission.id"), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    versions = relationship(
        "DraftVersion",
        back_populates="draft",
        order_by="DraftVersion.version_number",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "assignment_id",
            "assessment_id",
            "question_id",
            "intern_id",
            name="uq_draft_assignment_intern",
        ),
        Index("ix_drafts_assignment_id", "assignment_id"),
        Index("ix_drafts_intern_id", "intern_id"),
        Index("ix_drafts_updated_at", "updated_at"),
        Index("ix_drafts_is_locked", "is_locked"),
    )

    def __repr__(self) -> str:
        return (
            f"<Draft id={self.id} assignment_id={self.assignment_id} "
            f"intern_id={self.intern_id} language={self.language} "
            f"is_locked={self.is_locked}>"
        )


class DraftVersion(Base):
    """Immutable snapshot of a draft at a specific point in time.

    Every autosave, reset, or explicit save creates a new DraftVersion row.
    Existing rows are never modified.
    """

    __tablename__ = "draft_versions"

    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(
        Integer,
        ForeignKey("drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False)
    code = Column(Text, nullable=False, default="")
    language = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    draft = relationship("Draft", back_populates="versions")

    __table_args__ = (
        UniqueConstraint(
            "draft_id",
            "version_number",
            name="uq_draft_version_number",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DraftVersion draft_id={self.draft_id} "
            f"version_number={self.version_number}>"
        )
