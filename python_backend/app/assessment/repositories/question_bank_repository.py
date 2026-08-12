# python_backend/app/assessment/repositories/question_bank_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.assessment.models.assessment import QuestionBank, Question

class QuestionBankRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, question_bank: QuestionBank) -> QuestionBank:
        self.db.add(question_bank)
        self.db.commit()
        self.db.refresh(question_bank)
        return question_bank

    def get_by_id(self, bank_id: int) -> Optional[QuestionBank]:
        return self.db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()

    def get_all(self) -> List[QuestionBank]:
        return self.db.query(QuestionBank).order_by(QuestionBank.created_at.desc()).all()

    def create_questions(self, questions: List[Question]) -> None:
        if questions:
            self.db.add_all(questions)
            self.db.commit()

    def get_questions_for_bank(self, bank_id: int) -> List[Question]:
        return self.db.query(Question).filter(Question.question_bank_id == bank_id).all()
    
    def get_all_questions(self) -> List[Question]:
        return self.db.query(Question).all()
