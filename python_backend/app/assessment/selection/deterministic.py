# python_backend/app/assessment/selection/deterministic.py
import random
from typing import List

from app.assessment.models.assessment import Assessment, Question
from app.assessment.selection.base import BaseQuestionSelectionProvider
from app.assessment.selection.validator import ConstraintValidator

class DeterministicFallbackSelector(BaseQuestionSelectionProvider):
    """Deterministically selects questions using a seeded PRNG based on assessment ID."""
    
    async def select_questions(
        self,
        assessment: Assessment,
        eligible_questions: List[Question],
        **kwargs
    ) -> List[int]:
        
        # Filter by topics
        if assessment.topic_tags:
            eligible_questions = [q for q in eligible_questions if q.topic in assessment.topic_tags]
            
        # Group by difficulty
        grouped = {"EASY": [], "MEDIUM": [], "HARD": []}
        for q in eligible_questions:
            diff = q.difficulty.value
            if diff in grouped:
                grouped[diff].append(q)
                
        # Seed PRNG for reproducibility
        seed = assessment.id if assessment.id else 42
        rng = random.Random(seed)
        
        # Sort each group for deterministic choice
        for diff in grouped:
            grouped[diff].sort(key=lambda x: (x.id, x.expected_time_minutes or 0))
            
        selected_ids = []
        required = assessment.difficulty_distribution
        
        for diff, req_count in required.items():
            if len(grouped[diff]) < req_count:
                raise ValueError(f"Insufficient questions for {diff}. Fallback failed.")
                
            # Randomly select the required number of questions from this difficulty
            chosen = rng.sample(grouped[diff], req_count)
            selected_ids.extend([q.id for q in chosen])
            
        return selected_ids
