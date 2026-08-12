# python_backend/app/assessment/services/assessment_service.py
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

from app.assessment.models.assessment import (
    Assessment, AssessmentQuestion, AssessmentIntern, Question, AssessmentStatusEnum
)
from app.assessment.repositories.assessment_repository import AssessmentRepository
from app.assessment.repositories.question_bank_repository import QuestionBankRepository
from app.assessment.schemas.assessment import AssessmentCreateRequest
from app.assessment.selection.factory import get_selection_provider
from app.assessment.selection.validator import ConstraintValidator

logger = logging.getLogger(__name__)

class AssessmentService:
    def __init__(self, db: Session):
        self.repo = AssessmentRepository(db)
        self.qb_repo = QuestionBankRepository(db)
        self.db = db

    def create_assessment(self, req: AssessmentCreateRequest) -> Assessment:
        if req.ai_selection_enabled:
            total_dist = sum(req.difficulty_distribution.values())
            if total_dist != req.total_questions:
                raise ValueError("Difficulty distribution total does not match total_questions.")
            
        status = AssessmentStatusEnum.GENERATED if req.question_ids else AssessmentStatusEnum.DRAFT
        
        ass = Assessment(
            title=req.title,
            duration_minutes=req.duration_minutes,
            total_questions=req.total_questions,
            difficulty_distribution=req.difficulty_distribution,
            topic_tags=req.topic_tags,
            ai_selection_enabled=req.ai_selection_enabled,
            status=status
        )
        created_ass = self.repo.create(ass)
        
        if req.question_ids:
            # Verify selected question IDs actually exist
            valid_questions = self.db.query(Question).filter(Question.id.in_(req.question_ids)).all()
            valid_ids = {q.id for q in valid_questions}
            missing_ids = set(req.question_ids) - valid_ids
            if missing_ids:
                raise ValueError(f"Questions with IDs {missing_ids} do not exist.")
                
            if req.question_bank_id:
                invalid_bank_questions = [q.id for q in valid_questions if q.question_bank_id != req.question_bank_id]
                if invalid_bank_questions:
                    raise ValueError(f"Questions with IDs {invalid_bank_questions} do not belong to bank {req.question_bank_id}.")
                
            aq_list = []
            for idx, q_id in enumerate(req.question_ids):
                aq_list.append(AssessmentQuestion(
                    assessment_id=created_ass.id,
                    question_id=q_id,
                    order_index=idx
                ))
            self.repo.create_assessment_questions(aq_list)
            
        return created_ass

    async def _select_and_validate(self, assessment: Assessment) -> List[Question]:
        all_questions = self.qb_repo.get_all_questions()
        
        # Fast fail if pool is obviously insufficient
        ConstraintValidator.validate_pool(assessment, all_questions)
        
        provider = get_selection_provider(use_ai=assessment.ai_selection_enabled)
        
        try:
            selected_ids = await provider.select_questions(assessment, all_questions)
            selected_questions = [q for q in all_questions if q.id in selected_ids]
            
            # Strict Validation
            ConstraintValidator.validate_selection(assessment, selected_questions)
            return selected_questions
            
        except Exception as e:
            logger.warning(f"Primary selection failed: {e}. Falling back to deterministic.")
            # Fallback
            fallback = get_selection_provider(use_ai=False)
            selected_ids = await fallback.select_questions(assessment, all_questions)
            selected_questions = [q for q in all_questions if q.id in selected_ids]
            ConstraintValidator.validate_selection(assessment, selected_questions)
            return selected_questions

    async def preview_selection(self, assessment_id: int) -> List[Question]:
        assessment = self.repo.get_by_id(assessment_id)
        if not assessment:
            raise ValueError("Assessment not found.")
            
        return await self._select_and_validate(assessment)

    async def generate_assessment(self, assessment_id: int) -> Assessment:
        assessment = self.repo.get_by_id(assessment_id)
        if not assessment:
            raise ValueError("Assessment not found.")
            
        if assessment.status not in [AssessmentStatusEnum.DRAFT, AssessmentStatusEnum.GENERATED]:
            raise ValueError(f"Cannot generate from status {assessment.status}")
            
        selected_questions = await self._select_and_validate(assessment)
        
        # Clear old generation if exists
        self.db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment_id).delete()
        
        # Insert new
        aq_list = []
        for idx, q in enumerate(selected_questions):
            aq_list.append(AssessmentQuestion(
                assessment_id=assessment.id,
                question_id=q.id,
                order_index=idx
            ))
            
        self.repo.create_assessment_questions(aq_list)
        
        assessment.status = AssessmentStatusEnum.GENERATED
        return self.repo.update(assessment)

    def publish_assessment(self, assessment_id: int) -> Assessment:
        assessment = self.repo.get_by_id(assessment_id)
        if not assessment:
            raise ValueError("Assessment not found.")
        if assessment.status != AssessmentStatusEnum.GENERATED:
            raise ValueError(f"Cannot publish from status {assessment.status}")
            
        assessment.status = AssessmentStatusEnum.PUBLISHED
        assessment.published_at = datetime.utcnow()
        return self.repo.update(assessment)

    def assign_assessment(self, assessment_id: int, intern_id: int) -> AssessmentIntern:
        assessment = self.repo.get_by_id(assessment_id)
        if not assessment:
            raise ValueError("Assessment not found.")
        if assessment.status not in [AssessmentStatusEnum.PUBLISHED, AssessmentStatusEnum.ASSIGNED]:
            raise ValueError("Assessment must be published to be assigned.")
            
        # Check if already assigned
        existing = self.repo.get_assignment(assessment_id, intern_id)
        if existing:
            raise ValueError("This intern is already assigned to this assessment.")
            
        assignment = AssessmentIntern(
            assessment_id=assessment_id,
            intern_id=intern_id
        )
        created = self.repo.create_assignment(assignment)
        
        if assessment.status == AssessmentStatusEnum.PUBLISHED:
            assessment.status = AssessmentStatusEnum.ASSIGNED
            self.repo.update(assessment)
            
        return created
