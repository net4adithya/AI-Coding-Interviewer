# python_backend/app/execution/models/execution_result.py
"""SQLAlchemy ExecutionResult model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from app.db.base_class import Base


class ExecutionResult(Base):
    """Persistent database record for individual test case execution.

    Contains normalized execution status, Judge0 status, runtime metrics,
    stdout/stderr, and expected vs actual output.
    """

    __tablename__ = "execution_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submission.id"), nullable=False, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False, index=True)
    provider = Column(String(64), nullable=False, default="judge0")
    language = Column(String(64), nullable=False)
    judge0_token = Column(String(128), nullable=True)

    status = Column(String(64), nullable=False, index=True, default="PENDING")
    status_id = Column(Integer, nullable=True)
    passed = Column(Boolean, nullable=False, default=False)

    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    compile_output = Column(Text, nullable=True)
    message = Column(Text, nullable=True)

    execution_time = Column(Float, nullable=True)  # in seconds
    memory = Column(Integer, nullable=True)  # in KB

    expected_output = Column(Text, nullable=True)
    actual_output = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("submission_id", "test_case_id", name="uq_submission_test_case_result"),
        Index("ix_execution_results_submission_status", "submission_id", "status"),
    )
