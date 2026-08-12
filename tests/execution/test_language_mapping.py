# tests/execution/test_language_mapping.py
"""Tests for Judge0 language mapping."""

import pytest
from app.execution.language.judge0_language_map import (
    get_judge0_language_id,
    is_language_supported,
    list_supported_languages,
)
from app.execution.exceptions import UnsupportedLanguageException

EXPECTED_LANGUAGES = [
    ("python", 71),
    ("java", 62),
    ("javascript", 63),
    ("typescript", 74),
    ("c", 50),
    ("cpp", 54),
    ("csharp", 51),
    ("go", 60),
    ("rust", 73),
    ("php", 68),
    ("kotlin", 78),
    ("swift", 83),
]


@pytest.mark.parametrize("lang,expected_id", EXPECTED_LANGUAGES)
def test_all_12_supported_languages(lang, expected_id):
    assert get_judge0_language_id(lang) == expected_id
    assert is_language_supported(lang) is True


def test_case_insensitive_mapping():
    assert get_judge0_language_id("PYTHON") == 71
    assert get_judge0_language_id("  Java  ") == 62


def test_unsupported_language_raises():
    assert is_language_supported("brainfuck") is False
    with pytest.raises(UnsupportedLanguageException):
        get_judge0_language_id("brainfuck")


def test_list_supported_languages():
    langs = list_supported_languages()
    assert len(langs) == 12
    assert "python" in langs
    assert "cpp" in langs
