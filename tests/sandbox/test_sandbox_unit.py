"""Tests for sandbox language resolution and schema validation."""

import pytest

from app.sandbox.language_config import resolve_language
from app.sandbox.schemas import ExecutionRequest, ExecutionStatus
from app.sandbox.executor import DockerSandboxExecutor, UnsupportedLanguageError


def test_resolve_supported_languages():
    assert resolve_language("python") is not None
    assert resolve_language("JavaScript") is not None
    assert resolve_language("cpp") is not None
    assert resolve_language("java") is not None


def test_reject_invalid_language():
    assert resolve_language("rust") is None
    assert resolve_language("bash") is None


def test_execution_request_schema():
    req = ExecutionRequest(
        question_id="q1",
        language="python",
        source_code="print(1)",
        stdin="",
    )
    assert req.language == "python"


def test_execution_status_enum_values():
    assert ExecutionStatus.ACCEPTED.value == "ACCEPTED"
    assert ExecutionStatus.TIME_LIMIT_EXCEEDED.value == "TIME_LIMIT_EXCEEDED"


def test_invalid_language_rejected():
    executor = DockerSandboxExecutor()
    with pytest.raises(UnsupportedLanguageError):
        executor.execute(language="fortran", source_code="print *, 1", stdin="")
