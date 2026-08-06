from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.session import get_db
from ai_review.services.ai_review_service import AIReviewService
from ai_review.schemas.ai_review import AIReviewResponse

router = APIRouter(prefix="/ai-review", tags=["AI Review"])

def get_ai_review_service(db: Session = Depends(get_db)) -> AIReviewService:
    return AIReviewService(db=db)

@router.get("/health", summary="Gemini Provider Health Check")
def health_check(service: AIReviewService = Depends(get_ai_review_service)) -> Dict[str, Any]:
    """Return health check status for the configured AI Provider."""
    return service.health_check()

@router.post("/trigger/{submission_id}", response_model=AIReviewResponse, summary="Trigger AI Code Review")
def trigger_review(submission_id: int, prompt_version: str = "v1", service: AIReviewService = Depends(get_ai_review_service)):
    """Trigger AI code review for a submission."""
    # Dummy mock submission object wrapper if database submission query is not attached
    class SubmissionDummy:
        def __init__(self, sub_id):
            self.id = sub_id
            self.code = "def add(a, b):\n    return a + b"
            self.language = "python"
            self.assignment_id = 1
            self.intern_id = 1

    try:
        submission = SubmissionDummy(submission_id)
        review = service.generate_and_save_review(submission, prompt_version=prompt_version)
        return AIReviewResponse.model_validate(review)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI Review: {str(exc)}")

@router.get("/{submission_id}", response_model=AIReviewResponse, summary="Get AI Code Review")
def get_review(submission_id: int, service: AIReviewService = Depends(get_ai_review_service)):
    """Get complete AI review for a submission."""
    review = service.get_review_by_submission(submission_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"AI Review not found for submission {submission_id}")
    return AIReviewResponse.model_validate(review)
