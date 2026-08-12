# python_backend/app/execution/services/execution_service.py
"""Core execution service orchestrating code execution and downstream pipeline triggers.

Pipeline sequence:
  Editor Submission → Judge0 Execution → Static Analysis → Gemini AI Review → Authority Review dashboard
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.execution.config import execution_settings
from app.execution.exceptions import (
    SubmissionNotFoundException,
    SubmissionNotFinalizedException,
    DuplicateExecutionException,
    CodeSizeLimitExceededException,
    ExecutionAccessDeniedError,
)
from app.execution.models.execution_result import ExecutionResult
from app.execution.models.test_case import TestCase
from app.execution.providers.base import BaseExecutionProvider, ExecutionRequest
from app.execution.providers.factory import get_execution_provider
from app.execution.repositories.execution_repository import ExecutionRepository
from app.execution.schemas.execution import (
    ExecutionSummaryResponse,
    ExecutionTestCaseResultResponse,
    ExecutionHealthResponse,
)
from app.execution.utils.result_normalizer import normalize_judge0_status, ExecutionStatusEnum
from static_analysis.models.static_analysis import Submission
from app.editor.models.editor import Draft

logger = logging.getLogger(__name__)


class ExecutionService:
    """Orchestrates test case execution with Judge0 and downstream pipelines."""

    def __init__(
        self,
        db: Session,
        execution_repo: Optional[ExecutionRepository] = None,
        provider: Optional[BaseExecutionProvider] = None,
    ):
        self.db = db
        self.repo = execution_repo or ExecutionRepository(db)
        self.provider = provider or get_execution_provider()

    # ── Pipeline Execution ────────────────────────────────────────────────────

    async def run_execution_pipeline(self, submission_id: int) -> ExecutionSummaryResponse:
        """Run the complete post-submission execution pipeline.

        1. Verify submission existence & lock state
        2. Prevent duplicate processing
        3. Load source code & language from Draft/Submission
        4. Load test cases (or create default smoke test)
        5. Execute test cases via provider (Judge0)
        6. Persist normalized execution results & compute aggregate stats
        7. Trigger Static Analysis module
        8. Trigger Gemini AI Review module
        9. Return aggregated execution summary
        """
        logger.info("[ExecutionService] Starting execution pipeline for submission %d", submission_id)

        # 1. Fetch submission
        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise SubmissionNotFoundException(submission_id)

        # 2. Check draft state and get code/language
        draft = self.db.query(Draft).filter(Draft.submission_id == submission_id).first()
        if not draft:
            # Fallback: check draft by draft_id if stored or latest locked draft
            raise SubmissionNotFinalizedException(submission_id)

        if not draft.is_locked or not draft.is_submitted:
            raise SubmissionNotFinalizedException(submission_id)

        # Check for duplicate execution
        existing_results = self.repo.get_results_by_submission(submission_id)
        if existing_results and submission.status in ("PROCESSING", "COMPLETED"):
            logger.info("[ExecutionService] Submission %d already processed/processing.", submission_id)
            return self.get_execution_summary(submission_id=submission_id, current_user_id=draft.intern_id, current_user_role="authority")

        # Mark submission status as PROCESSING
        submission.status = "PROCESSING"
        self.db.commit()

        source_code = draft.code or ""
        language = draft.language

        # Validate source code size limit
        code_bytes = len(source_code.encode("utf-8"))
        if code_bytes > execution_settings.MAX_SOURCE_CODE_SIZE:
            submission.status = "FAILED"
            self.db.commit()
            raise CodeSizeLimitExceededException(code_bytes, execution_settings.MAX_SOURCE_CODE_SIZE)

        # 3. Load or initialize test cases
        if draft.question_id:
            test_cases = self.repo.get_test_cases_by_question(draft.question_id)
        else:
            test_cases = self.repo.get_test_cases_by_assignment(draft.assignment_id)
            
        if not test_cases:
            # Default smoke test case if none configured for assignment
            smoke_test = TestCase(
                assignment_id=draft.assignment_id,
                question_id=draft.question_id,
                stdin="",
                expected_output="",
                is_hidden=False,
                weight=1.0,
                time_limit_sec=10.0,
                memory_limit_mb=512,
            )
            smoke_test = self.repo.create_test_case(smoke_test)
            test_cases = [smoke_test]

        # Limit max test cases
        test_cases = test_cases[: execution_settings.MAX_TEST_CASES_PER_SUBMISSION]

        # 4. Execute each test case via Judge0 provider
        for tc in test_cases:
            req = ExecutionRequest(
                submission_id=submission_id,
                test_case_id=tc.id,
                language=language,
                source_code=source_code,
                stdin=tc.stdin or "",
                expected_output=tc.expected_output or "",
                time_limit_sec=tc.time_limit_sec,
                memory_limit_mb=tc.memory_limit_mb,
            )

            try:
                raw_result = await self.provider.execute(req)
                status_enum, passed, desc = normalize_judge0_status(raw_result.status_id)

                # Output evaluation: if status is PASSED (3) and expected_output is provided, check output match
                stdout_str = (raw_result.stdout or "").strip()
                expected_str = (tc.expected_output or "").strip()
                if tc.expected_output and status_enum == ExecutionStatusEnum.PASSED:
                    if stdout_str != expected_str:
                        status_enum = ExecutionStatusEnum.WRONG_ANSWER
                        passed = False

                exec_result = ExecutionResult(
                    submission_id=submission_id,
                    test_case_id=tc.id,
                    provider=self.provider.provider_name(),
                    language=language,
                    judge0_token=raw_result.token,
                    status=status_enum.value,
                    status_id=raw_result.status_id,
                    passed=passed,
                    stdout=raw_result.stdout,
                    stderr=raw_result.stderr,
                    compile_output=raw_result.compile_output,
                    message=raw_result.message or desc,
                    execution_time=raw_result.execution_time,
                    memory=raw_result.memory,
                    expected_output=tc.expected_output,
                    actual_output=raw_result.stdout,
                )
                self.repo.save_execution_result(exec_result)
            except Exception as exc:
                logger.error("[ExecutionService] Test case %d execution failed: %s", tc.id, str(exc))
                exec_result = ExecutionResult(
                    submission_id=submission_id,
                    test_case_id=tc.id,
                    provider=self.provider.provider_name(),
                    language=language,
                    status=ExecutionStatusEnum.INTERNAL_ERROR.value,
                    status_id=13,
                    passed=False,
                    message=str(exc),
                )
                self.repo.save_execution_result(exec_result)

        # Mark submission status as COMPLETED
        submission.status = "COMPLETED"
        self.db.commit()

        # 5. Trigger downstream Static Analysis
        try:
            self._trigger_static_analysis(submission_id, draft.assignment_id, draft.intern_id, language, source_code)
        except Exception as sa_err:
            logger.warning("[ExecutionService] Static Analysis trigger failed for submission %d: %s", submission_id, sa_err)

        # 6. Trigger downstream Gemini AI Review
        try:
            self._trigger_ai_review(submission, draft, source_code, language)
        except Exception as ai_err:
            logger.warning("[ExecutionService] Gemini AI Review trigger failed for submission %d: %s", submission_id, ai_err)

        logger.info("[ExecutionService] Execution pipeline completed successfully for submission %d", submission_id)
        return self.get_execution_summary(submission_id=submission_id, current_user_id=draft.intern_id, current_user_role="authority")

    # ── Downstream Pipeline Integration Triggers ─────────────────────────────

    def _trigger_static_analysis(self, submission_id: int, assignment_id: int, intern_id: int, language: str, source_code: str):
        """Invoke existing Static Analysis module synchronously or via task."""
        from static_analysis.services.static_analysis_service import StaticAnalysisService
        from static_analysis.repositories.static_analysis_repository import StaticAnalysisRepository
        from static_analysis.schemas.static_analysis import StaticAnalysisCreate

        sa_repo = StaticAnalysisRepository(self.db)
        sa_service = StaticAnalysisService(sa_repo)

        dto = StaticAnalysisCreate(
            submission_id=submission_id,
            assignment_id=assignment_id,
            intern_id=intern_id,
            language=language,
            source_code=source_code,
        )
        sa_service.analyze_code(dto)
        logger.info("[ExecutionService] Static Analysis completed for submission %d", submission_id)

    def _trigger_ai_review(self, submission, draft, source_code: str, language: str):
        """Invoke existing Gemini AI Review module with execution evidence in prompt context."""
        from ai_review.services.ai_review_service import AIReviewService
        
        # Attach language and attributes to submission object so prompt_builder gets full context
        setattr(submission, "language", language)
        setattr(submission, "assignment_id", draft.assignment_id)
        setattr(submission, "intern_id", draft.intern_id)
        setattr(submission, "code", source_code)

        stats = self.repo.get_aggregated_stats(submission.id)
        setattr(submission, "execution_stats", stats)

        ai_service = AIReviewService(db=self.db)
        ai_service.generate_and_save_review(submission)
        logger.info("[ExecutionService] Gemini AI Review completed for submission %d", submission.id)

    # ── Retrieval & Reporting ──────────────────────────────────────────────────

    def get_execution_summary(
        self, submission_id: int, current_user_id: int, current_user_role: str
    ) -> ExecutionSummaryResponse:
        """Get aggregated execution summary and individual test case outcomes."""
        draft = self.db.query(Draft).filter(Draft.submission_id == submission_id).first()
        if not draft:
            raise SubmissionNotFoundException(submission_id)

        # Access control check: intern can only read their own submission
        if current_user_role.lower() != "authority" and draft.intern_id != current_user_id:
            raise ExecutionAccessDeniedError()

        stats = self.repo.get_aggregated_stats(submission_id)
        raw_results = self.repo.get_results_by_submission(submission_id)

        results_dto: List[ExecutionTestCaseResultResponse] = []
        is_authority = current_user_role.lower() == "authority"

        for r in raw_results:
            tc = self.repo.get_test_case_by_id(r.test_case_id)
            is_hidden = tc.is_hidden if tc else False

            # Mask hidden test case data for interns
            stdin_val = r.stdout if (is_authority or not is_hidden) else None
            expected_val = r.expected_output if (is_authority or not is_hidden) else None
            actual_val = r.actual_output if (is_authority or not is_hidden) else None

            item = ExecutionTestCaseResultResponse(
                id=r.id,
                submission_id=r.submission_id,
                test_case_id=r.test_case_id,
                provider=r.provider,
                language=r.language,
                status=r.status,
                passed=r.passed,
                stdout=stdin_val,
                stderr=r.stderr if (is_authority or not is_hidden) else None,
                compile_output=r.compile_output,
                message=r.message,
                execution_time=r.execution_time,
                memory=r.memory,
                stdin=r.actual_output if (is_authority or not is_hidden) else None,
                expected_output=expected_val,
                actual_output=actual_val,
                is_hidden=is_hidden,
                created_at=r.created_at,
            )
            results_dto.append(item)

        return ExecutionSummaryResponse(
            submission_id=submission_id,
            status=stats["execution_status"],
            total_test_cases=stats["total_test_cases"],
            passed_test_cases=stats["passed_test_cases"],
            failed_test_cases=stats["failed_test_cases"],
            pass_percentage=stats["pass_percentage"],
            max_execution_time=stats["maximum_execution_time"],
            avg_execution_time=stats["average_execution_time"],
            max_memory=stats["maximum_memory"],
            avg_memory=stats["average_memory"],
            compilation_success=stats["compilation_success"],
            results=results_dto,
        )

    def get_result_detail(
        self, result_id: int, current_user_id: int, current_user_role: str
    ) -> ExecutionTestCaseResultResponse:
        """Get single test case execution result detail."""
        res = self.repo.get_result_by_id(result_id)
        if not res:
            raise SubmissionNotFoundException(result_id)

        draft = self.db.query(Draft).filter(Draft.submission_id == res.submission_id).first()
        if draft and current_user_role.lower() != "authority" and draft.intern_id != current_user_id:
            raise ExecutionAccessDeniedError()

        tc = self.repo.get_test_case_by_id(res.test_case_id)
        is_hidden = tc.is_hidden if tc else False
        is_authority = current_user_role.lower() == "authority"

        return ExecutionTestCaseResultResponse(
            id=res.id,
            submission_id=res.submission_id,
            test_case_id=res.test_case_id,
            provider=res.provider,
            language=res.language,
            status=res.status,
            passed=res.passed,
            stdout=res.stdout if (is_authority or not is_hidden) else None,
            stderr=res.stderr if (is_authority or not is_hidden) else None,
            compile_output=res.compile_output,
            message=res.message,
            execution_time=res.execution_time,
            memory=res.memory,
            expected_output=res.expected_output if (is_authority or not is_hidden) else None,
            actual_output=res.actual_output if (is_authority or not is_hidden) else None,
            is_hidden=is_hidden,
            created_at=res.created_at,
        )

    async def get_health(self) -> ExecutionHealthResponse:
        """Return provider health and availability."""
        health_data = await self.provider.health_check()
        return ExecutionHealthResponse(
            provider=health_data.get("provider", "judge0"),
            configured=health_data.get("configured", False),
            available=health_data.get("available", False),
            version=health_data.get("version"),
        )
