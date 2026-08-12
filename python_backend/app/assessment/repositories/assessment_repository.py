# python_backend/app/assessment/repositories/assessment_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.assessment.models.assessment import Assessment, AssessmentQuestion, AssessmentIntern, Question

class AssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, assessment: Assessment) -> Assessment:
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_by_id(self, assessment_id: int) -> Optional[Assessment]:
        return self.db.query(Assessment).filter(Assessment.id == assessment_id).first()

    def get_all(self) -> List[Assessment]:
        return self.db.query(Assessment).all()

    def update(self, assessment: Assessment) -> Assessment:
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def create_assessment_questions(self, questions: List[AssessmentQuestion]) -> None:
        if questions:
            self.db.add_all(questions)
            self.db.commit()

    def get_assessment_questions(self, assessment_id: int) -> List[Question]:
        return (
            self.db.query(Question)
            .join(AssessmentQuestion, AssessmentQuestion.question_id == Question.id)
            .filter(AssessmentQuestion.assessment_id == assessment_id)
            .order_by(AssessmentQuestion.order_index)
            .all()
        )

    def create_assignment(self, assignment: AssessmentIntern) -> AssessmentIntern:
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
        
    def get_assignment(self, assessment_id: int, intern_id: int) -> Optional[AssessmentIntern]:
        return self.db.query(AssessmentIntern).filter(
            AssessmentIntern.assessment_id == assessment_id,
            AssessmentIntern.intern_id == intern_id
        ).first()

    def get_assignments_for_intern(self, intern_id: int) -> List[AssessmentIntern]:
        return self.db.query(AssessmentIntern).filter(
            AssessmentIntern.intern_id == intern_id
        ).all()
