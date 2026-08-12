# python_backend/app/routers/dashboard.py
"""Dashboard router for Authority."""

from fastapi import APIRouter, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.assessment.api.dependencies import require_authority, get_assessment_service
from app.assessment.services.assessment_service import AssessmentService
from app.assessment.models.assessment import Assessment, AssessmentIntern, AuthorityDecision
from app.users.models import User
from sqlalchemy import desc

router = APIRouter()

class RecentAssessmentSchema(BaseModel):
    id: int
    title: str
    questions: int
    interns: int
    status: str
    created_at: datetime
    deadline_at: Optional[datetime] = None

class CandidateActivitySchema(BaseModel):
    intern_name: str
    assessment_title: str
    action: str
    timestamp: datetime

class DashboardStatsResponse(BaseModel):
    active_assessments: int
    interns_count: int
    submissions_count: int
    pending_reviews: int
    recent_assessments: List[RecentAssessmentSchema]
    candidate_activity: List[CandidateActivitySchema]

@router.get("/authority/stats", response_model=DashboardStatsResponse)
def get_authority_stats(
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(require_authority)
):
    """Get dashboard stats for authority."""
    db = ass_service.repo.db

    active_assessments = db.query(Assessment).filter(Assessment.status != 'DRAFT').count()
    interns_count = db.query(User).filter(User.role == 'intern').count()
    
    submissions_count = db.query(AssessmentIntern).filter(AssessmentIntern.submitted_at != None).count()
    pending_reviews = db.query(AssessmentIntern).outerjoin(AuthorityDecision).filter(
        AssessmentIntern.submitted_at != None,
        AuthorityDecision.id == None
    ).count()

    recent_assessments_db = db.query(Assessment).order_by(desc(Assessment.created_at)).limit(5).all()
    recent_assessments = []
    for ass in recent_assessments_db:
        interns_for_ass = db.query(AssessmentIntern).filter(AssessmentIntern.assessment_id == ass.id).count()
        recent_assessments.append(RecentAssessmentSchema(
            id=ass.id,
            title=ass.title,
            questions=ass.total_questions,
            interns=interns_for_ass,
            status=ass.status.value if hasattr(ass.status, 'value') else ass.status,
            created_at=ass.created_at,
            deadline_at=None  # Currently no deadline field exists
        ))

    recent_activities_db = db.query(AssessmentIntern, User, Assessment)\
        .join(User, AssessmentIntern.intern_id == User.id)\
        .join(Assessment, AssessmentIntern.assessment_id == Assessment.id)\
        .filter(AssessmentIntern.status != 'ASSIGNED')\
        .order_by(desc(AssessmentIntern.updated_at))\
        .limit(5).all()

    candidate_activity = []
    for ai, u, a in recent_activities_db:
        action = "updated"
        ts = ai.updated_at or ai.assigned_at
        if ai.submitted_at and ai.status == 'COMPLETED':
            action = "submitted"
            ts = ai.submitted_at
        elif ai.started_at:
            action = "started"
            ts = ai.started_at
            
        candidate_activity.append(CandidateActivitySchema(
            intern_name=u.email.split('@')[0],
            assessment_title=a.title,
            action=action,
            timestamp=ts
        ))

    return DashboardStatsResponse(
        active_assessments=active_assessments,
        interns_count=interns_count,
        submissions_count=submissions_count,
        pending_reviews=pending_reviews,
        recent_assessments=recent_assessments,
        candidate_activity=candidate_activity
    )
