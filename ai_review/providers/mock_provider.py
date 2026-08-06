from typing import Dict, Any
from ai_review.providers.base_provider import BaseAIProvider
from ai_review.services.prompt_builder import ReviewPromptContext

class MockAIProvider(BaseAIProvider):
    def provider_name(self) -> str:
        return "MockAI"

    def provider_version(self) -> str:
        return "1.0.0"

    def generate_review(self, context: ReviewPromptContext) -> Dict[str, Any]:
        return {
            "review_status": "COMPLETED",
            "overall_score": 85.0,
            "correctness_score": 85.0,
            "algorithm_score": 85.0,
            "time_complexity_score": 80.0,
            "space_complexity_score": 85.0,
            "readability_score": 80.0,
            "maintainability_score": 78.0,
            "best_practices_score": 82.0,
            "security_score": 75.0,
            "performance_score": 88.0,
            "edge_case_score": 80.0,
            "confidence_score": 90.0,
            "recommendation": "PASS",
            "time_complexity": "O(N log N)",
            "space_complexity": "O(N)",
            "ai_summary": "The submission is well-structured with minor readability issues.",
            "strengths": ["Clear function naming", "Good modularization"],
            "weaknesses": ["Lack of input validation", "Missing docstrings"],
            "recommendations": ["Add validation", "Include docstrings"],
            "score_reasoning": {"correctness": "Standard inputs work seamlessly."},
            "code_issue_snippets": [],
            "optimized_alternatives": [],
            "expected_improvements": {},
            "review_trace": {"rules": ["mock_rule_1"]},
            "structured_findings": {"security": "Clean"},
            "provider": self.provider_name(),
            "provider_version": self.provider_version(),
            "model_name": "MockModel-v1",
            "review_duration_ms": 120,
            "prompt_version": context.prompt_version or "v1",
            "temperature": 0.2,
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "available": True,
            "provider": self.provider_name(),
            "version": self.provider_version(),
            "model": "MockModel-v1",
            "status": "HEALTHY",
        }
