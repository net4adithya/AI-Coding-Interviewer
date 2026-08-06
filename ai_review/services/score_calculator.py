from typing import Dict, Any

RUBRIC_WEIGHTS = {
    "correctness_score": 0.30,
    "algorithm_score": 0.15,
    "time_complexity_score": 0.10,
    "space_complexity_score": 0.05,
    "readability_score": 0.10,
    "maintainability_score": 0.10,
    "best_practices_score": 0.05,
    "security_score": 0.05,
    "optimization_score": 0.05,
    "edge_case_score": 0.05,
}

class ScoreCalculator:
    """Computes backend weighted overall score deterministically from metric scores."""

    @staticmethod
    def calculate_overall_score(metrics: Dict[str, float]) -> float:
        overall = 0.0
        for key, weight in RUBRIC_WEIGHTS.items():
            score = float(metrics.get(key, 0.0))
            # Clamp individual metric score between 0 and 100
            score = max(0.0, min(100.0, score))
            overall += score * weight
        return round(overall, 2)
