import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from ai_review.providers.gemini_provider import GeminiProvider
from ai_review.services.prompt_builder import ReviewPromptContext
from ai_review.config import GeminiConfig

@pytest.fixture
def mock_gemini_config():
    return GeminiConfig(
        api_key="test_api_key",
        model_name="gemini-3.6-flash",
        temperature=0.2,
        max_output_tokens=2048,
        request_timeout=10.0
    )

def test_gemini_provider_generate_review(mock_gemini_config):
    provider = GeminiProvider(config=mock_gemini_config)

    valid_response_json = {
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
        "confidence_score": 92.0,
        "recommendation": "PASS",
        "time_complexity": "O(N)",
        "space_complexity": "O(1)",
        "summary": "Good algorithm",
        "strengths": ["Clean code"],
        "weaknesses": ["None"],
        "optimization_suggestions": ["Vectorize loop"]
    }

    mock_urlopen = MagicMock()
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": json.dumps(valid_response_json)}
                    ]
                }
            }
        ]
    }).encode("utf-8")
    mock_urlopen.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_urlopen):
        context = ReviewPromptContext(
            source_code="def add(a,b): return a+b",
            programming_language="python",
            submission_id=1
        )
        review = provider.generate_review(context)
        assert review["review_status"] == "COMPLETED"
        assert review["overall_score"] is not None
        assert review["correctness_score"] == 90.0
        assert review["recommendation"] == "PASS"

def test_gemini_provider_health_check_healthy(mock_gemini_config):
    provider = GeminiProvider(config=mock_gemini_config)
    mock_urlopen = MagicMock()
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "candidates": [{"content": {"parts": [{"text": "{\"status\": \"ok\"}"}]}}]
    }).encode("utf-8")
    mock_urlopen.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_urlopen):
        health = provider.health_check()
        assert health["available"] is True
        assert health["status"] == "HEALTHY"
