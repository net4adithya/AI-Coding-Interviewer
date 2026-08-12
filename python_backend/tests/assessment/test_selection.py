# tests/assessment/test_selection.py
import pytest
from typing import Dict, Any

from app.assessment.models.assessment import Assessment, Question, DifficultyEnum
from app.assessment.selection.validator import ConstraintValidator
from app.assessment.selection.deterministic import DeterministicFallbackSelector

def create_mock_question(id: int, difficulty: str, topic: str = "General", time: int = 15) -> Question:
    q = Question(
        title=f"Question {id}",
        problem_statement="Do something",
        topic=topic,
        difficulty=DifficultyEnum(difficulty),
        expected_time_minutes=time
    )
    q.id = id
    return q

def test_validator_pool():
    assessment = Assessment(
        title="Test",
        duration_minutes=60,
        total_questions=3,
        difficulty_distribution={"EASY": 1, "MEDIUM": 2},
        topic_tags=["General"]
    )
    
    pool = [
        create_mock_question(1, "EASY"),
        create_mock_question(2, "MEDIUM"),
        create_mock_question(3, "MEDIUM"),
    ]
    
    # Should pass
    assert ConstraintValidator.validate_pool(assessment, pool) is True
    
    # Should fail due to missing Medium
    pool_short = pool[:2]
    with pytest.raises(ValueError, match="Insufficient questions for difficulty MEDIUM"):
        ConstraintValidator.validate_pool(assessment, pool_short)

def test_validator_selection():
    assessment = Assessment(
        title="Test",
        duration_minutes=60,
        total_questions=3,
        difficulty_distribution={"EASY": 1, "MEDIUM": 2},
        topic_tags=["General"]
    )
    
    selected = [
        create_mock_question(1, "EASY"),
        create_mock_question(2, "MEDIUM"),
        create_mock_question(3, "MEDIUM"),
    ]
    
    # Should pass
    assert ConstraintValidator.validate_selection(assessment, selected) is True
    
    # Fail on count
    with pytest.raises(ValueError, match="Selected 2 questions"):
        ConstraintValidator.validate_selection(assessment, selected[:2])

@pytest.mark.asyncio
async def test_deterministic_selector():
    assessment = Assessment(
        title="Test",
        duration_minutes=60,
        total_questions=3,
        difficulty_distribution={"EASY": 1, "MEDIUM": 2},
        topic_tags=None
    )
    assessment.id = 1
    
    pool = [
        create_mock_question(1, "EASY"),
        create_mock_question(2, "EASY"),
        create_mock_question(3, "MEDIUM"),
        create_mock_question(4, "MEDIUM"),
        create_mock_question(5, "HARD"),
    ]
    
    selector = DeterministicFallbackSelector()
    ids = await selector.select_questions(assessment, pool)
    
    assert len(ids) == 3
    # With seed 1, choice should be deterministic
    assert set(ids) == {1, 3, 4} # Note: Randomness might vary based on RNG seed logic, but just check length and difficulty
    
    selected = [q for q in pool if q.id in ids]
    assert ConstraintValidator.validate_selection(assessment, selected) is True
