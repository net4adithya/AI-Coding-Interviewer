# python_backend/app/editor/repositories/template_repository.py
"""Concrete filesystem-based template repository.

Templates are stored under:
    python_backend/templates/{language}/starter.{ext}

Adding support for a new language requires only placing the file in the
correct folder – no code changes needed.
"""

import os
from typing import List

from app.editor.exceptions import UnsupportedLanguageError
from app.editor.interfaces.template_repository import Template, TemplateRepositoryInterface


# Map language identifier → (directory name, starter filename)
_LANGUAGE_FILE_MAP: dict[str, str] = {
    "python":     "starter.py",
    "java":       "starter.java",
    "javascript": "starter.js",
    "typescript": "starter.ts",
    "c":          "starter.c",
    "cpp":        "starter.cpp",
    "csharp":     "starter.cs",
    "go":         "starter.go",
    "rust":       "starter.rs",
    "php":        "starter.php",
    "kotlin":     "starter.kt",
    "swift":      "starter.swift",
}

# Root of all templates – resolved relative to this file's location:
#   python_backend/app/editor/repositories/template_repository.py
#   → up 3 levels → python_backend/
#   → templates/
_backend_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_TEMPLATES_ROOT = os.path.join(_backend_dir, "templates")
if not os.path.isdir(_TEMPLATES_ROOT):
    # Fallback if templates directory is at project root
    _TEMPLATES_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "templates")
    )


class FileSystemTemplateRepository(TemplateRepositoryInterface):
    """Reads starter templates from the filesystem."""

    def __init__(self, templates_root: str = _TEMPLATES_ROOT):
        self._templates_root = templates_root

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_template(self, language: str) -> Template:
        """Return the starter template for *language*.

        Args:
            language: Case-insensitive language identifier.

        Returns:
            Template dataclass with language, filename, and code.

        Raises:
            UnsupportedLanguageError: If the language is not in the
                supported set or its file cannot be found.
        """
        normalized = language.lower().strip()

        if normalized not in _LANGUAGE_FILE_MAP:
            raise UnsupportedLanguageError(language)

        filename = _LANGUAGE_FILE_MAP[normalized]
        file_path = os.path.join(self._templates_root, normalized, filename)

        if not os.path.isfile(file_path):
            # Template file missing from disk – treat as unsupported language
            raise UnsupportedLanguageError(language)

        with open(file_path, "r", encoding="utf-8") as fh:
            code = fh.read()

        return Template(language=normalized, filename=filename, code=code)

    def list_supported_languages(self) -> List[str]:
        """Return all configured language identifiers (lowercase)."""
        return list(_LANGUAGE_FILE_MAP.keys())
