# python_backend/app/assessment/selection/factory.py
from app.assessment.selection.base import BaseQuestionSelectionProvider
from app.assessment.selection.deterministic import DeterministicFallbackSelector
from app.assessment.selection.gemini import GeminiQuestionSelectionProvider

def get_selection_provider(use_ai: bool = True) -> BaseQuestionSelectionProvider:
    """Factory to get the appropriate question selection provider."""
    
    if use_ai:
        provider = GeminiQuestionSelectionProvider()
        # Fall back to deterministic if AI is not configured
        if provider.model:
            return provider
            
    return DeterministicFallbackSelector()
