import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, Index
from app.db.base_class import Base

class ReviewStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESUBMISSION_REQUESTED = "RESUBMISSION_REQUESTED"

class ReviewDecisionEnum(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RESUBMIT = "RESUBMIT"

class AuthorityReview(Base):
    __tablename__ = "authority_reviews"
    __table_args__ = (
        Index('idx_authority_submission_id', 'submission_id'),
        Index('idx_authority_assignment_id', 'assignment_id'),
        Index('idx_authority_intern_id', 'intern_id'),
        Index('idx_authority_reviewer_id', 'reviewer_id'),
        Index('idx_authority_status', 'status'),
        Index('idx_authority_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, nullable=False, default=lambda: str(uuid4()))
    submission_id = Column(Integer, ForeignKey("submission.id"), unique=True, nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignment.id"), nullable=True)
    intern_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    status = Column(Enum(ReviewStatusEnum), nullable=False, default=ReviewStatusEnum.PENDING)
    decision = Column(Enum(ReviewDecisionEnum), nullable=True)
    internal_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    review_version = Column(String, nullable=True)
    review_source = Column(String, nullable=True)
    ai_provider = Column(String, nullable=True)
    model_name = Column(String, nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
