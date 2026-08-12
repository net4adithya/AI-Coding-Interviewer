import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum, ForeignKey, Index, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Submission(Base):
    __tablename__ = "submission"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    status = Column(String, nullable=True)

class Assignment(Base):
    __tablename__ = "assignment"
    id = Column(Integer, primary_key=True, index=True)


class AnalysisStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class StaticAnalysis(Base):
    __tablename__ = "static_analysis"
    __table_args__ = (
        Index('idx_submission_id', 'submission_id'),
        Index('idx_assignment_id', 'assignment_id'),
        Index('idx_intern_id', 'intern_id'),
        Index('idx_language', 'language'),
        Index('idx_analysis_status', 'analysis_status'),
        Index('idx_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, nullable=False, default=lambda: str(uuid4()))
    submission_id = Column(Integer, ForeignKey("submission.id"), unique=True, nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignment.id"), nullable=True)
    intern_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    language = Column(String, nullable=False)

    analysis_status = Column(Enum(AnalysisStatusEnum), nullable=False, default=AnalysisStatusEnum.PENDING)

    lines_of_code = Column(Integer, nullable=True)
    blank_lines = Column(Integer, nullable=True)
    comment_lines = Column(Integer, nullable=True)
    comment_ratio = Column(Float, nullable=True)
    cyclomatic_complexity = Column(Integer, nullable=True)
    cognitive_complexity = Column(Integer, nullable=True)
    maintainability_index = Column(Float, nullable=True)
    duplicate_lines = Column(Integer, nullable=True)
    duplicate_percentage = Column(Float, nullable=True)
    function_count = Column(Integer, nullable=True)
    class_count = Column(Integer, nullable=True)
    variable_count = Column(Integer, nullable=True)
    maximum_nesting_depth = Column(Integer, nullable=True)
    security_warning_count = Column(Integer, nullable=True)
    style_violation_count = Column(Integer, nullable=True)
    code_smell_count = Column(Integer, nullable=True)
    analysis_duration_ms = Column(Integer, nullable=True)
    analyzer_name = Column(String, nullable=True)
    analyzer_version = Column(String, nullable=True)
    structured_output = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
