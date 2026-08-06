import logging
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session

from ai_review.models.ai_review import AIReview, ReviewStatusEnum
from ai_review.repositories.ai_review_repository import AIReviewRepository
from ai_review.providers.base_provider import BaseAIProvider
from ai_review.providers.factory import get_ai_provider
from ai_review.services.prompt_builder import ReviewPromptContext, build_context

logger = logging.getLogger("ai_review.service")

class AIReviewService:
    """Orchestrates AI Code Review generation and management."""

    def __init__(self, db: Session, repository: Optional[AIReviewRepository] = None, provider: Optional[BaseAIProvider] = None):
        self.db = db
        self.repository = repository or AIReviewRepository()
        self.provider = provider or get_ai_provider()

    def generate_and_save_review(self, submission, prompt_version: str = "v1") -> AIReview:
        """Trigger AI code review for a submission and persist complete structured metrics."""
        submission_id = submission.id

        # Check for existing review
        existing = self.repository.get_by_submission_id(self.db, submission_id)
        if existing and existing.review_status == ReviewStatusEnum.COMPLETED:
            return existing

        context = build_context(submission, prompt_version=prompt_version)

        # Create or update pending review record
        if not existing:
            review_record = AIReview(
                submission_id=submission_id,
                assignment_id=getattr(submission, "assignment_id", None),
                intern_id=getattr(submission, "intern_id", None),
                language=getattr(submission, "language", "python"),
                review_status=ReviewStatusEnum.PROCESSING,
                prompt_version=prompt_version,
            )
            review_record = self.repository.create(self.db, review_record)
        else:
            existing.review_status = ReviewStatusEnum.PROCESSING
            review_record = self.repository.update(self.db, existing)

        try:
            review_output = self.provider.generate_review(context)
            
            # Map review output to database model fields
            review_record.review_status = ReviewStatusEnum.COMPLETED
            review_record.overall_score = review_output.get("overall_score")
            review_record.correctness_score = review_output.get("correctness_score")
            review_record.algorithm_score = review_output.get("algorithm_score")
            review_record.time_complexity_score = review_output.get("time_complexity_score")
            review_record.space_complexity_score = review_output.get("space_complexity_score")
            review_record.readability_score = review_output.get("readability_score")
            review_record.maintainability_score = review_output.get("maintainability_score")
            review_record.best_practices_score = review_output.get("best_practices_score")
            review_record.security_score = review_output.get("security_score")
            review_record.performance_score = review_output.get("performance_score")
            review_record.edge_case_score = review_output.get("edge_case_score")
            review_record.confidence_score = review_output.get("confidence_score")
            review_record.recommendation = review_output.get("recommendation")
            
            review_record.time_complexity = review_output.get("time_complexity")
            review_record.space_complexity = review_output.get("space_complexity")
            review_record.ai_summary = review_output.get("ai_summary")
            review_record.strengths = review_output.get("strengths")
            review_record.weaknesses = review_output.get("weaknesses")
            review_record.recommendations = review_output.get("recommendations")

            review_record.score_reasoning = review_output.get("score_reasoning")
            review_record.code_issue_snippets = review_output.get("code_issue_snippets")
            review_record.optimized_alternatives = review_output.get("optimized_alternatives")
            review_record.expected_improvements = review_output.get("expected_improvements")
            review_record.review_trace = review_output.get("review_trace")
            review_record.structured_findings = review_output.get("structured_findings")

            review_record.provider = review_output.get("provider")
            review_record.provider_version = review_output.get("provider_version")
            review_record.model_name = review_output.get("model_name")
            review_record.review_duration_ms = review_output.get("review_duration_ms")
            review_record.temperature = review_output.get("temperature")

            return self.repository.update(self.db, review_record)
        except Exception as exc:
            logger.error(f"Failed to generate AI Review for submission {submission_id}: {exc}")
            review_record.review_status = ReviewStatusEnum.FAILED
            self.repository.update(self.db, review_record)
            raise exc

    def get_review_by_submission(self, submission_id: int) -> Optional[AIReview]:
        return self.repository.get_by_submission_id(self.db, submission_id)

    def health_check(self) -> Dict[str, Any]:
        return self.provider.health_check()
