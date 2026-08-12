# tests/execution/test_execution_service.py
"""Tests for ExecutionService orchestration and downstream triggers."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.execution.services.execution_service import ExecutionService
from app.execution.repositories.execution_repository import ExecutionRepository
from app.execution.providers.base import BaseExecutionProvider, ExecutionRawResult
from app.execution.exceptions import (
    SubmissionNotFoundException,
    SubmissionNotFinalizedException,
    CodeSizeLimitExceededException,
)
from app.execution.models.test_case import TestCase


def make_mock_provider():
    provider = MagicMock(spec=BaseExecutionProvider)
    provider.provider_name.return_value = "judge0"
    provider.provider_version.return_value = "v1"
    provider.execute = AsyncMock(
        return_value=ExecutionRawResult(
            token="tok-mock",
            status_id=3,
            status_description="Accepted",
            stdout="hello\n",
            execution_time=0.04,
            memory=14000,
        )
    )
    return provider


def test_run_execution_pipeline_success(db, sample_submission):
    async def _test():
        provider = make_mock_provider()
        repo = ExecutionRepository(db)
        svc = ExecutionService(db=db, execution_repo=repo, provider=provider)

        with patch.object(svc, "_trigger_static_analysis") as mock_sa, patch.object(
            svc, "_trigger_ai_review"
        ) as mock_ai:
            summary = await svc.run_execution_pipeline(sample_submission.id)

        assert summary.submission_id == sample_submission.id
        assert summary.passed_test_cases == 1
        assert summary.pass_percentage == 100.0
        assert mock_sa.called
        assert mock_ai.called

    asyncio.run(_test())


def test_nonexistent_submission_raises(db):
    async def _test():
        svc = ExecutionService(db=db, provider=make_mock_provider())
        with pytest.raises(SubmissionNotFoundException):
            await svc.run_execution_pipeline(99999)

    asyncio.run(_test())


def test_code_size_limit_exceeded(db, sample_submission, monkeypatch):
    async def _test():
        import app.execution.services.execution_service as svc_mod
        monkeypatch.setattr(svc_mod.execution_settings, "MAX_SOURCE_CODE_SIZE", 5)

        svc = ExecutionService(db=db, provider=make_mock_provider())
        with pytest.raises(CodeSizeLimitExceededException):
            await svc.run_execution_pipeline(sample_submission.id)

    asyncio.run(_test())
