# tests/execution/test_execution_permissions.py
"""Permissions and hidden test case filtering tests."""

import pytest
from app.execution.services.execution_service import ExecutionService
from app.execution.repositories.execution_repository import ExecutionRepository
from app.execution.models.test_case import TestCase
from app.execution.models.execution_result import ExecutionResult
from app.execution.exceptions import ExecutionAccessDeniedError


def test_intern_cannot_view_other_submission_results(db, sample_submission):
    repo = ExecutionRepository(db)
    svc = ExecutionService(db=db, execution_repo=repo)

    with pytest.raises(ExecutionAccessDeniedError):
        # User ID 999 is trying to view Intern 10's submission
        svc.get_execution_summary(
            submission_id=sample_submission.id,
            current_user_id=999,
            current_user_role="intern",
        )


def test_hidden_test_case_data_masked_for_interns(db, sample_submission, sample_assignment):
    repo = ExecutionRepository(db)
    tc_hidden = repo.create_test_case(
        TestCase(
            assignment_id=sample_assignment.id,
            stdin="secret_input",
            expected_output="secret_output",
            is_hidden=True,
        )
    )

    res = ExecutionResult(
        submission_id=sample_submission.id,
        test_case_id=tc_hidden.id,
        provider="judge0",
        language="python",
        status="PASSED",
        passed=True,
        stdout="secret_output",
        expected_output="secret_output",
        actual_output="secret_output",
    )
    repo.save_execution_result(res)

    svc = ExecutionService(db=db, execution_repo=repo)

    # 1. Intern view -> hidden input/outputs must be None
    intern_summary = svc.get_execution_summary(
        submission_id=sample_submission.id,
        current_user_id=10,
        current_user_role="intern",
    )
    tc_res = intern_summary.results[0]
    assert tc_res.passed is True
    assert tc_res.stdout is None
    assert tc_res.expected_output is None

    # 2. Authority view -> complete input/outputs visible
    auth_summary = svc.get_execution_summary(
        submission_id=sample_submission.id,
        current_user_id=999,
        current_user_role="authority",
    )
    auth_tc_res = auth_summary.results[0]
    assert auth_tc_res.stdout == "secret_output"
    assert auth_tc_res.expected_output == "secret_output"
