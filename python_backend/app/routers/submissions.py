# python_backend/app/routers/submissions.py
"""Submissions router for Authority."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.users.models import User
from app.assessment.models.assessment import AssessmentIntern, Assessment
from app.assessment.api.dependencies import require_authority
from static_analysis.models.static_analysis import Submission, StaticAnalysis
from authority_review.models.authority_review import AuthorityReview

router = APIRouter()

class SubmissionResponse(BaseModel):
    id: int
    intern_name: str
    intern_email: str
    assessment_title: str
    submitted_at: datetime
    language: str
    ai_review_status: str
    review_status: str
    submission_id: int # The actual submission ID for review

    class Config:
        orm_mode = True

@router.get("/", response_model=List[SubmissionResponse])
def get_submissions(
    db: Session = Depends(get_db),
    user_ctx: dict = Depends(require_authority)
):
    """Get all submissions for Authority."""
    # We join AssessmentIntern with Assessment, User, and Submission.
    # Submission table has assessment_id. Wait, does it have intern_id?
    # Usually we can join Draft -> Submission or just use AssessmentIntern.
    # Let's try joining Submission on assessment_id. But there are multiple questions?
    # For Phase 12, we can just grab Submissions where assessment_id is present.
    # Actually, let's fetch Drafts that are submitted to get the submission_id, 
    # or join Submission directly if it has assignment_id/assessment_id and we correlate with User.
    
    # Since Submission might only have assessment_id and question_id, we can join Draft to get intern_id.
    from app.editor.models.editor import Draft
    
    query = (
        db.query(Draft, AssessmentIntern, User, Assessment, AuthorityReview)
        .join(AssessmentIntern, (Draft.intern_id == AssessmentIntern.intern_id) & (Draft.assessment_id == AssessmentIntern.assessment_id))
        .join(User, Draft.intern_id == User.id)
        .join(Assessment, Draft.assessment_id == Assessment.id)
        .outerjoin(AuthorityReview, Draft.submission_id == AuthorityReview.submission_id)
        .filter(Draft.is_submitted == True)
        .filter(Draft.submission_id != None)
        .order_by(AssessmentIntern.submitted_at.desc())
    )
    
    results = query.all()
    
    response = []
    for draft, ai, user, assessment, auth_rev in results:
        response.append(SubmissionResponse(
            id=draft.id,
            intern_name=getattr(user, "name", user.email.split("@")[0]),
            intern_email=user.email,
            assessment_title=assessment.title,
            submitted_at=ai.submitted_at or draft.updated_at,
            language=draft.language,
            ai_review_status="COMPLETED" if auth_rev else "PENDING", # Simplified for now
            review_status=auth_rev.status.value if auth_rev and hasattr(auth_rev.status, "value") else (auth_rev.status if auth_rev else "PENDING"),
            submission_id=draft.submission_id
        ))
        
    return response
