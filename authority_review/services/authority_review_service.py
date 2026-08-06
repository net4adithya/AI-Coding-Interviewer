import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from ..models.authority_review import AuthorityReview, ReviewStatusEnum, ReviewDecisionEnum
from ..repositories.authority_review_repository import AuthorityReviewRepository
from ..schemas.authority_review import (
    AuthorityReviewAggregatedResponse,
    AuthorityReviewDetailsResponse,
    SubmissionInfoResponse,
    AIReviewSectionResponse,
    StaticAnalysisSectionResponse,
    DockerExecutionSectionResponse,
)
from ..exceptions.exceptions import (
    AuthorityReviewNotFoundException,
    SubmissionNotFoundException,
    DuplicateAuthorityReviewException,
)
from ..utils.audit_logger import AuditLogger
from ..utils.event_publisher import InMemoryEventPublisher

# Imports for fetching related models if present in DB
from static_analysis.models.static_analysis import StaticAnalysis
try:
    from ai_review.models.ai_review import AIReview
except ImportError:
    AIReview = None

class AuthorityReviewService:
    """Service layer for Authority Review operations."""

    def __init__(self, db: Session, repository: AuthorityReviewRepository, event_publisher: InMemoryEventPublisher = None):
        self.db = db
        self.repository = repository
        self.event_publisher = event_publisher or InMemoryEventPublisher()

    def get_or_create_review(self, submission_id: int, reviewer_id: Optional[int] = None) -> Tuple[AuthorityReview, bool]:
        """Fetch existing review or initialize with status UNDER_REVIEW."""
        review = self.repository.get_by_submission_id(submission_id)
        created = False
        if not review:
            review = AuthorityReview(
                request_id=str(uuid.uuid4()),
                submission_id=submission_id,
                reviewer_id=reviewer_id,
                status=ReviewStatusEnum.UNDER_REVIEW,
            )
            review = self.repository.create(review)
            created = True
            AuditLogger.log_event(
                "authority_review_opened",
                submission_id=submission_id,
                reviewer_id=reviewer_id,
                details={"request_id": review.request_id, "status": review.status.value},
            )
        return review, created

    def get_aggregated_review(self, submission_id: int, reviewer_id: Optional[int] = None) -> AuthorityReviewAggregatedResponse:
        """Aggregate submission data, AI Review, Static Analysis, Docker execution placeholder, and Authority Review."""
        # 1. Get or create AuthorityReview
        review, _ = self.get_or_create_review(submission_id, reviewer_id=reviewer_id)

        # 2. Retrieve Static Analysis data if available
        static_analysis_record = (
            self.db.query(StaticAnalysis)
            .filter(StaticAnalysis.submission_id == submission_id, StaticAnalysis.is_deleted == False)
            .first()
        )
        static_analysis_section = None
        if static_analysis_record:
            static_analysis_section = StaticAnalysisSectionResponse(
                cyclomatic_complexity=static_analysis_record.cyclomatic_complexity,
                maintainability_index=static_analysis_record.maintainability_index,
                security_warnings=static_analysis_record.security_warning_count,
                code_smells=static_analysis_record.code_smell_count,
                duplicate_code={
                    "lines": static_analysis_record.duplicate_lines,
                    "percentage": static_analysis_record.duplicate_percentage,
                },
                unused_variables=0,
                structured_output=static_analysis_record.structured_output or {},
            )

        # 3. Retrieve AI Review data if available
        ai_review_section = None
        if AIReview:
            ai_record = (
                self.db.query(AIReview)
                .filter(AIReview.submission_id == submission_id, AIReview.is_deleted == False)
                .first()
            )
            if ai_record:
                ai_review_section = AIReviewSectionResponse(
                    overall_score=getattr(ai_record, "overall_score", None),
                    recommendation=getattr(ai_record, "recommendation", None),
                    confidence=getattr(ai_record, "confidence_score", None),
                    strengths=getattr(ai_record, "strengths", []),
                    weaknesses=getattr(ai_record, "weaknesses", []),
                    optimization_suggestions=getattr(ai_record, "recommendations", []),
                    complexity_analysis=getattr(ai_record, "complexity_analysis", {}),
                    security_review=getattr(ai_record, "security_review", {}),
                    performance_review=getattr(ai_record, "performance_review", {}),
                )

        # 4. Submission Information
        submission_info = SubmissionInfoResponse(
            submission_id=submission_id,
            assignment_id=review.assignment_id,
            intern_id=review.intern_id,
            language=static_analysis_record.language if static_analysis_record else "python",
            status=review.status.value,
            submission_timestamp=review.created_at,
        )

        # 5. Docker Execution Placeholder
        docker_section = DockerExecutionSectionResponse(
            execution_time_ms=None,
            memory_usage_mb=None,
            cpu_usage_percent=None,
            hidden_test_results=None,
            is_placeholder=True,
        )

        # 6. Authority Review Details
        authority_details = AuthorityReviewDetailsResponse(
            id=review.id,
            request_id=review.request_id,
            submission_id=review.submission_id,
            assignment_id=review.assignment_id,
            intern_id=review.intern_id,
            reviewer_id=review.reviewer_id,
            status=review.status.value,
            decision=review.decision.value if review.decision else None,
            internal_notes=review.internal_notes,
            reviewed_at=review.reviewed_at,
            review_version=review.review_version,
            review_source=review.review_source,
            ai_provider=review.ai_provider,
            model_name=review.model_name,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )

        return AuthorityReviewAggregatedResponse(
            submission=submission_info,
            ai_review=ai_review_section,
            static_analysis=static_analysis_section,
            docker_execution=docker_section,
            authority_review=authority_details,
        )

    def _update_submission_status(self, submission_id: int, new_status: str) -> None:
        """Helper to cascade status update to the submission entity if present."""
        try:
            from sqlalchemy import text
            self.db.execute(
                text("UPDATE submission SET status = :status WHERE id = :id"),
                {"status": new_status, "id": submission_id},
            )
            self.db.commit()
        except Exception:
            self.db.rollback()

    def approve_submission(self, submission_id: int, reviewer_id: int, internal_notes: Optional[str] = None) -> AuthorityReviewDetailsResponse:
        review, _ = self.get_or_create_review(submission_id, reviewer_id=reviewer_id)
        review.status = ReviewStatusEnum.APPROVED
        review.decision = ReviewDecisionEnum.APPROVE
        review.reviewer_id = reviewer_id
        review.reviewed_at = datetime.utcnow()
        if internal_notes is not None:
            review.internal_notes = internal_notes

        review = self.repository.update(review)
        self._update_submission_status(submission_id, "APPROVED")

        AuditLogger.log_event(
            "authority_review_approved",
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            details={"decision": "APPROVE", "notes": internal_notes},
        )
        self.event_publisher.publish_event(
            "submission_approved",
            {"submission_id": submission_id, "reviewer_id": reviewer_id, "status": "APPROVED"},
        )
        return AuthorityReviewDetailsResponse.model_validate(review)

    def reject_submission(self, submission_id: int, reviewer_id: int, internal_notes: Optional[str] = None) -> AuthorityReviewDetailsResponse:
        review, _ = self.get_or_create_review(submission_id, reviewer_id=reviewer_id)
        review.status = ReviewStatusEnum.REJECTED
        review.decision = ReviewDecisionEnum.REJECT
        review.reviewer_id = reviewer_id
        review.reviewed_at = datetime.utcnow()
        if internal_notes is not None:
            review.internal_notes = internal_notes

        review = self.repository.update(review)
        self._update_submission_status(submission_id, "REJECTED")

        AuditLogger.log_event(
            "authority_review_rejected",
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            details={"decision": "REJECT", "notes": internal_notes},
        )
        self.event_publisher.publish_event(
            "submission_rejected",
            {"submission_id": submission_id, "reviewer_id": reviewer_id, "status": "REJECTED"},
        )
        return AuthorityReviewDetailsResponse.model_validate(review)

    def request_resubmission(self, submission_id: int, reviewer_id: int, internal_notes: Optional[str] = None) -> AuthorityReviewDetailsResponse:
        review, _ = self.get_or_create_review(submission_id, reviewer_id=reviewer_id)
        review.status = ReviewStatusEnum.RESUBMISSION_REQUESTED
        review.decision = ReviewDecisionEnum.RESUBMIT
        review.reviewer_id = reviewer_id
        review.reviewed_at = datetime.utcnow()
        if internal_notes is not None:
            review.internal_notes = internal_notes

        review = self.repository.update(review)
        self._update_submission_status(submission_id, "RESUBMISSION_REQUIRED")

        AuditLogger.log_event(
            "authority_review_resubmission_requested",
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            details={"decision": "RESUBMIT", "notes": internal_notes},
        )
        self.event_publisher.publish_event(
            "submission_resubmission_requested",
            {"submission_id": submission_id, "reviewer_id": reviewer_id, "status": "RESUBMISSION_REQUIRED"},
        )
        return AuthorityReviewDetailsResponse.model_validate(review)

    def add_internal_notes(self, submission_id: int, reviewer_id: int, internal_notes: str) -> AuthorityReviewDetailsResponse:
        review = self.repository.get_by_submission_id(submission_id)
        if not review:
            review, _ = self.get_or_create_review(submission_id, reviewer_id=reviewer_id)

        review.internal_notes = internal_notes
        review.reviewer_id = reviewer_id
        review = self.repository.update(review)

        AuditLogger.log_event(
            "authority_notes_added",
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            details={"notes_length": len(internal_notes)},
        )
        return AuthorityReviewDetailsResponse.model_validate(review)

    def list_reviews(
        self,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        assignment_id: Optional[int] = None,
        intern_id: Optional[int] = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> Tuple[int, List[AuthorityReview]]:
        size = min(max(size, 1), 100)
        page = max(page, 1)
        skip = (page - 1) * size

        filters = {}
        if status is not None:
            filters["status"] = status
        if assignment_id is not None:
            filters["assignment_id"] = assignment_id
        if intern_id is not None:
            filters["intern_id"] = intern_id

        return self.repository.list(
            skip=skip,
            limit=size,
            filters=filters,
            sort_by=sort_by,
            order=order,
        )
