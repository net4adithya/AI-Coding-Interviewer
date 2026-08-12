# python_backend/app/execution/repositories/execution_repository.py
"""Database repository for test cases and execution results."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.execution.models.test_case import TestCase
from app.execution.models.execution_result import ExecutionResult
from app.execution.utils.result_normalizer import ExecutionStatusEnum


class ExecutionRepository:
    """Encapsulates CRUD operations and summary metrics calculation for code execution."""

    def __init__(self, db: Session):
        self.db = db

    # ── Test Cases ────────────────────────────────────────────────────────────

    def create_test_case(self, test_case: TestCase) -> TestCase:
        self.db.add(test_case)
        self.db.commit()
        self.db.refresh(test_case)
        return test_case

    def get_test_cases_by_assignment(self, assignment_id: int) -> List[TestCase]:
        return (
            self.db.query(TestCase)
            .filter(TestCase.assignment_id == assignment_id)
            .order_by(TestCase.id.asc())
            .all()
        )

    def get_test_cases_by_question(self, question_id: int) -> List[TestCase]:
        return (
            self.db.query(TestCase)
            .filter(TestCase.question_id == question_id)
            .order_by(TestCase.id.asc())
            .all()
        )

    def get_test_case_by_id(self, test_case_id: int) -> Optional[TestCase]:
        return self.db.query(TestCase).filter(TestCase.id == test_case_id).first()

    # ── Execution Results ──────────────────────────────────────────────────────

    def save_execution_result(self, result: ExecutionResult) -> ExecutionResult:
        """Upsert execution result for a submission and test case."""
        existing = (
            self.db.query(ExecutionResult)
            .filter(
                ExecutionResult.submission_id == result.submission_id,
                ExecutionResult.test_case_id == result.test_case_id,
            )
            .first()
        )

        if existing:
            existing.provider = result.provider
            existing.language = result.language
            existing.judge0_token = result.judge0_token
            existing.status = result.status
            existing.status_id = result.status_id
            existing.passed = result.passed
            existing.stdout = result.stdout
            existing.stderr = result.stderr
            existing.compile_output = result.compile_output
            existing.message = result.message
            existing.execution_time = result.execution_time
            existing.memory = result.memory
            existing.expected_output = result.expected_output
            existing.actual_output = result.actual_output
            self.db.commit()
            self.db.refresh(existing)
            return existing

        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def get_results_by_submission(self, submission_id: int) -> List[ExecutionResult]:
        return (
            self.db.query(ExecutionResult)
            .filter(ExecutionResult.submission_id == submission_id)
            .order_by(ExecutionResult.test_case_id.asc())
            .all()
        )

    def get_result_by_id(self, result_id: int) -> Optional[ExecutionResult]:
        return self.db.query(ExecutionResult).filter(ExecutionResult.id == result_id).first()

    def get_result_by_submission_and_test_case(
        self, submission_id: int, test_case_id: int
    ) -> Optional[ExecutionResult]:
        return (
            self.db.query(ExecutionResult)
            .filter(
                ExecutionResult.submission_id == submission_id,
                ExecutionResult.test_case_id == test_case_id,
            )
            .first()
        )

    # ── Aggregate Statistics ───────────────────────────────────────────────────

    def get_aggregated_stats(self, submission_id: int) -> Dict[str, Any]:
        results = self.get_results_by_submission(submission_id)
        if not results:
            return {
                "total_test_cases": 0,
                "passed_test_cases": 0,
                "failed_test_cases": 0,
                "pass_percentage": 0.0,
                "maximum_execution_time": 0.0,
                "average_execution_time": 0.0,
                "maximum_memory": 0,
                "average_memory": 0.0,
                "compilation_success": True,
                "execution_status": "PENDING",
            }

        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        failed_count = total - passed_count
        pass_pct = round((passed_count / total) * 100.0, 2) if total > 0 else 0.0

        exec_times = [r.execution_time for r in results if r.execution_time is not None]
        max_time = round(max(exec_times), 3) if exec_times else 0.0
        avg_time = round(sum(exec_times) / len(exec_times), 3) if exec_times else 0.0

        memories = [r.memory for r in results if r.memory is not None]
        max_mem = max(memories) if memories else 0
        avg_mem = round(sum(memories) / len(memories), 2) if memories else 0.0

        has_compile_error = any(
            r.status == ExecutionStatusEnum.COMPILATION_ERROR for r in results
        )
        compilation_success = not has_compile_error

        # Determine overall status
        if has_compile_error:
            overall_status = ExecutionStatusEnum.COMPILATION_ERROR.value
        elif any(r.status == ExecutionStatusEnum.RUNTIME_ERROR for r in results):
            overall_status = ExecutionStatusEnum.RUNTIME_ERROR.value
        elif any(r.status == ExecutionStatusEnum.TIME_LIMIT_EXCEEDED for r in results):
            overall_status = ExecutionStatusEnum.TIME_LIMIT_EXCEEDED.value
        elif any(r.status == ExecutionStatusEnum.MEMORY_LIMIT_EXCEEDED for r in results):
            overall_status = ExecutionStatusEnum.MEMORY_LIMIT_EXCEEDED.value
        elif failed_count > 0:
            overall_status = ExecutionStatusEnum.WRONG_ANSWER.value
        else:
            overall_status = ExecutionStatusEnum.PASSED.value

        return {
            "total_test_cases": total,
            "passed_test_cases": passed_count,
            "failed_test_cases": failed_count,
            "pass_percentage": pass_pct,
            "maximum_execution_time": max_time,
            "average_execution_time": avg_time,
            "maximum_memory": max_mem,
            "average_memory": avg_mem,
            "compilation_success": compilation_success,
            "execution_status": overall_status,
        }
