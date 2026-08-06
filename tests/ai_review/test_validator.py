import pytest
from ai_review.services.validator import ResponseValidator

def test_validator_valid_response():
    data = {
        "correctness_score": 90.0,
        "algorithm_score": 85.0,
        "time_complexity_score": 80.0,
        "space_complexity_score": 85.0,
        "readability_score": 90.0,
        "maintainability_score": 85.0,
        "best_practices_score": 80.0,
        "security_score": 95.0,
        "optimization_score": 80.0,
        "edge_case_score": 75.0,
        "recommendation": "PASS",
        "strengths": ["Clean code"],
    }
    ResponseValidator.validate(data)  # Should pass without exception

def test_validator_missing_metric():
    data = {
        "correctness_score": 90.0,
        "algorithm_score": 85.0,
        # missing time_complexity_score
    }
    with pytest.raises(ValueError, match="Missing required metric score"):
        ResponseValidator.validate(data)

def test_validator_out_of_bounds_score():
    data = {
        "correctness_score": 150.0,  # invalid range > 100
        "algorithm_score": 85.0,
        "time_complexity_score": 80.0,
        "space_complexity_score": 85.0,
        "readability_score": 90.0,
        "maintainability_score": 85.0,
        "best_practices_score": 80.0,
        "security_score": 95.0,
        "optimization_score": 80.0,
        "edge_case_score": 75.0,
    }
    with pytest.raises(ValueError, match="out of range"):
        ResponseValidator.validate(data)
