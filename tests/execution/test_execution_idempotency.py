# tests/execution/test_execution_idempotency.py
"""Tests for duplicate execution prevention and idempotency."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.execution.services.execution_service import ExecutionService
from app.execution.repositories.execution_repository import ExecutionRepository
from app.execution.models.execution_result import ExecutionResult
from app.execution.providers.base import BaseExecutionProvider, ExecutionRawResult


def test_duplicate_execution_returns_existing_summary(db, sample_submission):
    repo = ExecutionRepository(db)
    # Save existing result
    repo.save_execution_result(
        ExecutionResult(
            submission_id=sample_submission.id,
            test_case_id=1,
            provider="judge0",
            language="python",
            status="PASSED",
            passed=True,
        )
    )
    sample_submission.status = "COMPLETED"
    db.commit()

    mock_provider = MagicMock(spec=BaseExecutionProvider)
    mock_provider.execute = AsyncMock()

    svc = ExecutionService(db=db, execution_repo=repo, provider=mock_provider)

    # Calling pipeline again on COMPLETED submission must return existing summary without calling provider.execute
    import asyncio
    summary = asyncio.run(svc.run_execution_pipeline(sample_submission.id))

    assert summary.submission_id == sample_submission.id
    assert not mock_provider.execute.called
