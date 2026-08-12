# python_backend/app/execution/models/test_case.py
"""SQLAlchemy TestCase model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
from app.db.base_class import Base


class TestCase(Base):
    """Represents a test case associated with an assignment.

    Contains stdin, expected_output, and flags indicating whether it is
    hidden/private from interns.
    """

    __tablename__ = "test_cases"
    __test__ = False

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignment.id"), nullable=True, index=True) # Modified to be nullable for assessments
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    stdin = Column(Text, nullable=False, default="")
    expected_output = Column(Text, nullable=False, default="")
    is_hidden = Column(Boolean, nullable=False, default=False, index=True)
    weight = Column(Float, nullable=False, default=1.0)
    time_limit_sec = Column(Float, nullable=False, default=10.0)
    memory_limit_mb = Column(Integer, nullable=False, default=512)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_test_cases_assignment_hidden", "assignment_id", "is_hidden"),
    )
