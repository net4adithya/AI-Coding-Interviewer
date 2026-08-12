# python_backend/app/execution/language/judge0_language_map.py
"""Centralized mapping between application language identifiers and Judge0 language IDs.

Supports all 12 Phase 7 languages:
  python, java, javascript, typescript, c, cpp, csharp, go, rust, php, kotlin, swift
"""

from typing import Dict, List
from app.execution.exceptions import UnsupportedLanguageException

# Official Judge0 CE Language IDs:
#   Python (3.8.1) -> 71
#   Java (OpenJDK 13.0.1) -> 62
#   JavaScript (Node.js 12.14.0) -> 63
#   TypeScript (3.7.4) -> 74
#   C (GCC 9.2.0) -> 50
#   C++ (GCC 9.2.0) -> 54
#   C# (Mono 6.6.0.161) -> 51
#   Go (1.13.5) -> 60
#   Rust (1.40.0) -> 73
#   PHP (7.4.1) -> 68
#   Kotlin (1.3.70) -> 78
#   Swift (5.2.3) -> 83

_JUDGE0_LANGUAGE_MAP: Dict[str, int] = {
    "python": 71,
    "java": 62,
    "javascript": 63,
    "typescript": 74,
    "c": 50,
    "cpp": 54,
    "csharp": 51,
    "go": 60,
    "rust": 73,
    "php": 68,
    "kotlin": 78,
    "swift": 83,
}


def get_judge0_language_id(language: str) -> int:
    """Return the numeric Judge0 language ID for a given language string.

    Args:
        language: Case-insensitive language identifier.

    Returns:
        Numeric Judge0 language ID.

    Raises:
        UnsupportedLanguageException: If language is not supported.
    """
    normalized = (language or "").strip().lower()
    if normalized not in _JUDGE0_LANGUAGE_MAP:
        raise UnsupportedLanguageException(language)
    return _JUDGE0_LANGUAGE_MAP[normalized]


def is_language_supported(language: str) -> bool:
    """Check whether a language string is supported."""
    normalized = (language or "").strip().lower()
    return normalized in _JUDGE0_LANGUAGE_MAP


def list_supported_languages() -> List[str]:
    """Return a list of all supported language identifiers (lowercase)."""
    return list(_JUDGE0_LANGUAGE_MAP.keys())
