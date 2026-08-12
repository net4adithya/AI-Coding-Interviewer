# python_backend/app/assessment/schemas/assessment.py
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class AssessmentCreateRequest(BaseModel):
    title: str
    duration_minutes: int
    total_questions: int
    difficulty_distribution: Dict[str, int] # e.g. {"EASY": 2, "MEDIUM": 2, "HARD": 1}
    topic_tags: Optional[List[str]] = None
    ai_selection_enabled: bool = True
    question_ids: Optional[List[int]] = None
    question_bank_id: Optional[int] = None

class AssessmentResponse(BaseModel):
    id: int
    title: str
    duration_minutes: int
    total_questions: int
    difficulty_distribution: Dict[str, int]
    topic_tags: Optional[List[str]]
    ai_selection_enabled: bool
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    assignment_id: Optional[int] = None

    class Config:
        orm_mode = True
        # Allow mutating fields after construction (used to inject assignment_id after from_orm)
        allow_mutation = True

class AssignAssessmentRequest(BaseModel):
    intern_id: int

class AssignAssessmentEmailRequest(BaseModel):
    email: str

class AssessmentInternResponse(BaseModel):
    id: int
    assessment_id: int
    intern_id: int
    status: str
    assigned_at: datetime
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class AuthorityDecisionRequest(BaseModel):
    decision: str
    reviewer_notes: Optional[str] = None

class AuthorityDecisionResponse(BaseModel):
    id: int
    assessment_intern_id: int
    decision: str
    reviewer_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

