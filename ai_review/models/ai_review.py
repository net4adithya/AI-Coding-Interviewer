import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum, ForeignKey, Index, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base_class import Base

class ReviewStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AIReview(Base):
    __tablename__ = "ai_review"
    __table_args__ = (
        Index('idx_ai_submission_id', 'submission_id'),
        Index('idx_ai_assignment_id', 'assignment_id'),
        Index('idx_ai_intern_id', 'intern_id'),
        Index('idx_ai_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, nullable=False, default=lambda: str(uuid4()))
    submission_id = Column(Integer, ForeignKey("submission.id"), unique=True, nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignment.id"), nullable=True)
    intern_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    language = Column(String, nullable=True)

    review_status = Column(Enum(ReviewStatusEnum), nullable=False, default=ReviewStatusEnum.PENDING)

    # Independent Weighted Evaluation Scores (0 - 100)
    overall_score = Column(Float, nullable=True)
    correctness_score = Column(Float, nullable=True)
    algorithm_score = Column(Float, nullable=True)
    time_complexity_score = Column(Float, nullable=True)
    space_complexity_score = Column(Float, nullable=True)
    readability_score = Column(Float, nullable=True)
    maintainability_score = Column(Float, nullable=True)
    best_practices_score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)  # Maps to optimization score
    edge_case_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)

    recommendation = Column(String, nullable=True)  # PASS | FAIL | REVIEW

    # Analysis & Explanations (JSON / Text)
    ai_summary = Column(Text, nullable=True)
    time_complexity = Column(String, nullable=True)
    space_complexity = Column(String, nullable=True)
    strengths = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    weaknesses = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    recommendations = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    
    # Detailed Interview-Quality Insights
    score_reasoning = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    code_issue_snippets = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    optimized_alternatives = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    expected_improvements = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    review_trace = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    structured_findings = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    future_review_sections = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    # Metadata & Telemetry
    provider = Column(String, nullable=True)
    provider_version = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    review_duration_ms = Column(Integer, nullable=True)
    prompt_version = Column(String, nullable=True)
    temperature = Column(Float, nullable=True)
    token_usage = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
