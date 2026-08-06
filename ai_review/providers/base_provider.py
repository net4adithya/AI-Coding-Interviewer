from abc import ABC, abstractmethod
from ai_review.services.prompt_builder import ReviewPromptContext
from typing import Dict, Any

class BaseAIProvider(ABC):
    """Abstract interface for AI review providers."""

    @abstractmethod
    def generate_review(self, context: ReviewPromptContext) -> Dict[str, Any]:
        """Generate a structured review and return a dict matching the AIReview schema."""
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return provider health status details."""
        raise NotImplementedError

    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def provider_version(self) -> str:
        raise NotImplementedError
