# python_backend/app/assessment/models/assessment.py
"""SQLAlchemy models for Assessment & Question Selection Engine."""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, Enum
)
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base_class import Base

class DifficultyEnum(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class AssessmentStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    PUBLISHED = "PUBLISHED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class QuestionBank(Base):
    """Tracks an Authority-uploaded question-bank document."""
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PROCESSING") # PROCESSING, COMPLETED, FAILED
    question_count = Column(Integer, nullable=False, default=0)
    parsing_errors = Column(JSONB, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Question(Base):
    """Normalized coding question extracted from a question bank."""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_bank_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String, nullable=False)
    problem_statement = Column(Text, nullable=False)
    topic = Column(String, nullable=False, index=True)
    difficulty = Column(Enum(DifficultyEnum), nullable=False, index=True)
    constraints = Column(Text, nullable=True)
    examples = Column(JSONB, nullable=True) # List of dicts {input, output, explanation}
    expected_time_minutes = Column(Integer, nullable=True)
    programming_languages = Column(JSONB, nullable=False) # List of supported language slugs
    starter_code = Column(JSONB, nullable=True) # Dict of {language_slug: code}

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Assessment(Base):
    """Authority's assessment configuration."""
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    
    # Example: {"EASY": 2, "MEDIUM": 2, "HARD": 1}
    difficulty_distribution = Column(JSONB, nullable=False)
    # Example: ["Linked List", "Arrays"]
    topic_tags = Column(JSONB, nullable=True) 

    ai_selection_enabled = Column(Boolean, nullable=False, default=True)
    status = Column(Enum(AssessmentStatusEnum), nullable=False, default=AssessmentStatusEnum.DRAFT, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)


class AssessmentQuestion(Base):
    """Immutable question set selected for a particular assessment."""
    __tablename__ = "assessment_questions"

    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
    order_index = Column(Integer, nullable=False)
    selection_metadata = Column(JSONB, nullable=True) # AI selection audit data


class AssessmentIntern(Base):
    """Assignment of an assessment to an intern."""
    __tablename__ = "assessment_interns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    intern_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    status = Column(String, nullable=False, default="ASSIGNED") # ASSIGNED, IN_PROGRESS, COMPLETED, EXPIRED
    
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    expired_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("assessment_id", "intern_id", name="uq_assessment_intern"),
    )

class DecisionEnum(str, enum.Enum):
    PENDING = "PENDING"
    RECOMMENDED = "RECOMMENDED"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"
    NEEDS_FURTHER_REVIEW = "NEEDS_FURTHER_REVIEW"

class AuthorityDecision(Base):
    """Authority's final decision for an intern's assessment."""
    __tablename__ = "authority_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_intern_id = Column(Integer, ForeignKey("assessment_interns.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    decision = Column(Enum(DecisionEnum), nullable=False, default=DecisionEnum.PENDING)
    reviewer_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

