# python_backend/app/assessment/schemas/question_bank.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.assessment.schemas.question import ParsedQuestionSchema

class QuestionBankResponse(BaseModel):
    id: int
    owner_id: int
    filename: str
    status: str
    question_count: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class QuestionBankDetailResponse(QuestionBankResponse):
    parsing_errors: Optional[List[str]] = None
    questions: Optional[List[ParsedQuestionSchema]] = None
