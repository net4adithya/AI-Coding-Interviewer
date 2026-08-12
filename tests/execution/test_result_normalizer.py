# tests/execution/test_result_normalizer.py
"""Tests for Judge0 result status normalizer."""

import pytest
from app.execution.utils.result_normalizer import (
    normalize_judge0_status,
    ExecutionStatusEnum,
)


def test_passed_status():
    enum_val, passed, desc = normalize_judge0_status(3)
    assert enum_val == ExecutionStatusEnum.PASSED
    assert passed is True
    assert desc == "Passed"


def test_wrong_answer_status():
    enum_val, passed, desc = normalize_judge0_status(4)
    assert enum_val == ExecutionStatusEnum.WRONG_ANSWER
    assert passed is False
    assert desc == "Wrong Answer"


def test_compilation_error_status():
    enum_val, passed, desc = normalize_judge0_status(6)
    assert enum_val == ExecutionStatusEnum.COMPILATION_ERROR
    assert passed is False


def test_runtime_error_statuses():
    for status_id in (7, 8, 9, 10, 11, 12):
        enum_val, passed, _ = normalize_judge0_status(status_id)
        assert enum_val == ExecutionStatusEnum.RUNTIME_ERROR
        assert passed is False


def test_time_limit_exceeded():
    enum_val, passed, desc = normalize_judge0_status(5)
    assert enum_val == ExecutionStatusEnum.TIME_LIMIT_EXCEEDED
    assert passed is False


def test_unknown_status_fallback():
    enum_val, passed, _ = normalize_judge0_status(999)
    assert enum_val == ExecutionStatusEnum.INTERNAL_ERROR
    assert passed is False
