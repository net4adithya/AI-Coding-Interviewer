# python_backend/app/assessment/selection/validator.py
from typing import List, Dict
from app.assessment.models.assessment import Assessment, Question

class ConstraintValidator:
    """Validates assessment constraints against a pool of questions and selected questions."""
    
    @staticmethod
    def validate_pool(assessment: Assessment, pool: List[Question]) -> bool:
        """
        Check if the pool contains enough questions to satisfy the constraints.
        Raises ValueError if constraints cannot be satisfied.
        """
        # Filter by topics
        if assessment.topic_tags:
            pool = [q for q in pool if q.topic in assessment.topic_tags]
            
        difficulty_counts = {"EASY": 0, "MEDIUM": 0, "HARD": 0}
        for q in pool:
            if q.difficulty.value in difficulty_counts:
                difficulty_counts[q.difficulty.value] += 1
                
        required = assessment.difficulty_distribution
        for diff, req_count in required.items():
            if difficulty_counts.get(diff, 0) < req_count:
                raise ValueError(
                    f"Insufficient questions for difficulty {diff}. "
                    f"Required: {req_count}, Available: {difficulty_counts.get(diff, 0)}"
                )
                
        return True
        
    @staticmethod
    def validate_selection(assessment: Assessment, selected_questions: List[Question]) -> bool:
        """
        Strictly validate that the selected questions exactly match the requirements.
        Raises ValueError if validation fails.
        """
        if len(selected_questions) != assessment.total_questions:
            raise ValueError(
                f"Selected {len(selected_questions)} questions, "
                f"but assessment requires {assessment.total_questions}."
            )
            
        # Check for duplicates
        ids = [q.id for q in selected_questions]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate questions found in selection.")
            
        # Check topics
        if assessment.topic_tags:
            for q in selected_questions:
                if q.topic not in assessment.topic_tags:
                    raise ValueError(f"Question {q.id} topic '{q.topic}' is not in allowed topics.")
                    
        # Check difficulty distribution
        difficulty_counts = {"EASY": 0, "MEDIUM": 0, "HARD": 0}
        for q in selected_questions:
            diff = q.difficulty.value
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            
        required = assessment.difficulty_distribution
        for diff, req_count in required.items():
            if difficulty_counts.get(diff, 0) != req_count:
                raise ValueError(
                    f"Difficulty mismatch for {diff}. "
                    f"Required: {req_count}, Selected: {difficulty_counts.get(diff, 0)}"
                )
                
        return True
