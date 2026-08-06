from typing import Dict, Any, List

REQUIRED_SCORES = [
    "correctness_score",
    "algorithm_score",
    "time_complexity_score",
    "space_complexity_score",
    "readability_score",
    "maintainability_score",
    "best_practices_score",
    "security_score",
    "optimization_score",
    "edge_case_score",
]

class ResponseValidator:
    """Validates structured JSON output from AI providers."""

    @staticmethod
    def validate(data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValueError("Response output must be a JSON dictionary.")

        for score_key in REQUIRED_SCORES:
            if score_key not in data:
                raise ValueError(f"Missing required metric score: {score_key}")
            score_val = data[score_key]
            if not isinstance(score_val, (int, float)):
                raise ValueError(f"Metric {score_key} must be a number, got {type(score_val)}")
            if score_val < 0 or score_val > 100:
                raise ValueError(f"Metric {score_key} out of range [0, 100]: {score_val}")

        for list_key in ["strengths", "weaknesses", "optimization_suggestions"]:
            if list_key in data and not isinstance(data[list_key], list):
                raise ValueError(f"Field {list_key} must be a list if present.")

        recommendation = data.get("recommendation", "REVIEW")
        if recommendation not in ["PASS", "FAIL", "REVIEW"]:
            raise ValueError(f"Invalid recommendation '{recommendation}'. Must be PASS, FAIL, or REVIEW.")
