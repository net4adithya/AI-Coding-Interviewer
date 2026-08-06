from ai_review.services.score_calculator import ScoreCalculator, RUBRIC_WEIGHTS

def test_weighted_score_perfect_100():
    metrics = {key: 100.0 for key in RUBRIC_WEIGHTS}
    overall = ScoreCalculator.calculate_overall_score(metrics)
    assert overall == 100.0

def test_weighted_score_partial():
    metrics = {
        "correctness_score": 100.0,    # 30 * 1.0 = 30
        "algorithm_score": 80.0,       # 15 * 0.8 = 12
        "time_complexity_score": 70.0, # 10 * 0.7 = 7
        "space_complexity_score": 60.0,# 5 * 0.6 = 3
        "readability_score": 90.0,     # 10 * 0.9 = 9
        "maintainability_score": 80.0, # 10 * 0.8 = 8
        "best_practices_score": 100.0, # 5 * 1.0 = 5
        "security_score": 100.0,       # 5 * 1.0 = 5
        "optimization_score": 80.0,    # 5 * 0.8 = 4
        "edge_case_score": 60.0,       # 5 * 0.6 = 3
    }
    # Total = 30 + 12 + 7 + 3 + 9 + 8 + 5 + 5 + 4 + 3 = 86.0
    overall = ScoreCalculator.calculate_overall_score(metrics)
    assert overall == 86.0

def test_weighted_score_clamping():
    metrics = {key: 150.0 for key in RUBRIC_WEIGHTS}
    overall = ScoreCalculator.calculate_overall_score(metrics)
    assert overall == 100.0
