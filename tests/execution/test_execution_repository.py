# tests/execution/test_execution_repository.py
"""Tests for ExecutionRepository CRUD and statistics aggregation."""

import pytest
from app.execution.models.test_case import TestCase
from app.execution.models.execution_result import ExecutionResult
from app.execution.repositories.execution_repository import ExecutionRepository


@pytest.fixture()
def repo(db):
    return ExecutionRepository(db)


def test_test_case_crud(db, repo, sample_assignment):
    tc = TestCase(
        assignment_id=sample_assignment.id,
        stdin="2 3",
        expected_output="5",
        is_hidden=False,
        time_limit_sec=5.0,
    )
    created = repo.create_test_case(tc)
    assert created.id is not None
    assert created.assignment_id == sample_assignment.id

    fetched = repo.get_test_cases_by_assignment(sample_assignment.id)
    assert len(fetched) == 1
    assert fetched[0].stdin == "2 3"


def test_save_and_aggregate_results(db, repo, sample_submission, sample_assignment):
    tc1 = repo.create_test_case(TestCase(assignment_id=sample_assignment.id, expected_output="5"))
    tc2 = repo.create_test_case(TestCase(assignment_id=sample_assignment.id, expected_output="10"))

    res1 = ExecutionResult(
        submission_id=sample_submission.id,
        test_case_id=tc1.id,
        provider="judge0",
        language="python",
        status="PASSED",
        status_id=3,
        passed=True,
        execution_time=0.10,
        memory=15000,
    )
    res2 = ExecutionResult(
        submission_id=sample_submission.id,
        test_case_id=tc2.id,
        provider="judge0",
        language="python",
        status="WRONG_ANSWER",
        status_id=4,
        passed=False,
        execution_time=0.20,
        memory=20000,
    )

    repo.save_execution_result(res1)
    repo.save_execution_result(res2)

    stats = repo.get_aggregated_stats(sample_submission.id)
    assert stats["total_test_cases"] == 2
    assert stats["passed_test_cases"] == 1
    assert stats["failed_test_cases"] == 1
    assert stats["pass_percentage"] == 50.0
    assert stats["maximum_execution_time"] == 0.20
    assert stats["maximum_memory"] == 20000
    assert stats["execution_status"] == "WRONG_ANSWER"


def test_uniqueness_constraint(db, repo, sample_submission, sample_assignment):
    tc = repo.create_test_case(TestCase(assignment_id=sample_assignment.id))
    r1 = ExecutionResult(
        submission_id=sample_submission.id,
        test_case_id=tc.id,
        provider="judge0",
        language="python",
        status="PASSED",
        passed=True,
    )
    repo.save_execution_result(r1)

    # Re-saving same (submission, test_case) upserts rather than duplicating
    r1_updated = ExecutionResult(
        submission_id=sample_submission.id,
        test_case_id=tc.id,
        provider="judge0",
        language="python",
        status="WRONG_ANSWER",
        passed=False,
    )
    repo.save_execution_result(r1_updated)

    all_results = repo.get_results_by_submission(sample_submission.id)
    assert len(all_results) == 1
    assert all_results[0].status == "WRONG_ANSWER"
