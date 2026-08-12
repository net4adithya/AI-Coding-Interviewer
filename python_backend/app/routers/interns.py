# python_backend/app/routers/interns.py
"""Interns/Candidates router."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.users.models import User
from app.assessment.models.assessment import AssessmentIntern, Assessment
from app.assessment.api.dependencies import require_authority

router = APIRouter()

class CandidateResponse(BaseModel):
    id: int
    intern_email: str
    intern_name: Optional[str]
    assessment_title: str
    status: str
    assigned_at: datetime
    submitted_at: Optional[datetime]
    assessment_id: int
    intern_id: int

    class Config:
        orm_mode = True

@router.get("/candidates", response_model=List[CandidateResponse])
def get_candidates(
    db: Session = Depends(get_db),
    user_ctx: dict = Depends(require_authority)
):
    """Get all candidates (AssessmentIntern assignments) for Authority."""
    assignments = (
        db.query(AssessmentIntern, User, Assessment)
        .join(User, AssessmentIntern.intern_id == User.id)
        .join(Assessment, AssessmentIntern.assessment_id == Assessment.id)
        .order_by(AssessmentIntern.assigned_at.desc())
        .all()
    )
    
    result = []
    for ai, u, a in assignments:
        result.append(CandidateResponse(
            id=ai.id,
            intern_email=u.email,
            intern_name=getattr(u, "name", u.email.split("@")[0]),
            assessment_title=a.title,
            status=ai.status,
            assigned_at=ai.assigned_at,
            submitted_at=ai.submitted_at,
            assessment_id=a.id,
            intern_id=u.id
        ))
    return result
