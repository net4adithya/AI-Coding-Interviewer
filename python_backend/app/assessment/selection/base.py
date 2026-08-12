# python_backend/app/assessment/selection/base.py
import abc
from typing import List, Dict, Any, Optional

from app.assessment.models.assessment import Assessment, Question

class BaseQuestionSelectionProvider(abc.ABC):
    """Abstract base class for question selection providers."""
    
    @abc.abstractmethod
    async def select_questions(
        self,
        assessment: Assessment,
        eligible_questions: List[Question],
        **kwargs
    ) -> List[int]:
        """
        Select a subset of questions that satisfy the assessment constraints.
        
        Args:
            assessment: The assessment configuration (constraints).
            eligible_questions: Pool of available normalized questions.
            
        Returns:
            List of selected question IDs.
        
        Raises:
            Exception: If selection fails or constraints cannot be met.
        """
        pass
