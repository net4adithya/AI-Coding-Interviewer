# python_backend/app/assessment/api/dependencies.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.editor.dependencies import get_db, get_current_user_context
from app.assessment.services.question_bank_service import QuestionBankService
from app.assessment.services.assessment_service import AssessmentService
from app.assessment.parsers.pdf_parser import PdfQuestionBankParser

def get_question_bank_service(db: Session = Depends(get_db)) -> QuestionBankService:
    parser = PdfQuestionBankParser()
    return QuestionBankService(db=db, parser=parser)

def get_assessment_service(db: Session = Depends(get_db)) -> AssessmentService:
    return AssessmentService(db=db)

def require_authority(user_ctx: Dict[str, Any] = Depends(get_current_user_context)) -> Dict[str, Any]:
    """Ensure the current user has AUTHORITY role."""
    role = user_ctx.get("role", "").lower()
    if role not in ["authority", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires AUTHORITY role."
        )
    return user_ctx

def require_intern(user_ctx: Dict[str, Any] = Depends(get_current_user_context)) -> Dict[str, Any]:
    """Ensure the current user has INTERN role."""
    role = user_ctx.get("role", "").lower()
    if role not in ["intern", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires INTERN role."
        )
    return user_ctx
