# tests/editor/test_template_repository.py
"""Tests for FileSystemTemplateRepository – all 12 languages."""

import os
import pytest

from app.editor.repositories.template_repository import (
    FileSystemTemplateRepository,
    _LANGUAGE_FILE_MAP,
)
from app.editor.exceptions import UnsupportedLanguageError

TEMPLATES_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "python_backend", "templates")
)

SUPPORTED_LANGUAGES = list(_LANGUAGE_FILE_MAP.keys())


@pytest.fixture()
def repo():
    return FileSystemTemplateRepository(templates_root=TEMPLATES_ROOT)


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_all_supported_languages(repo, lang):
    """Every configured language must have a readable template file."""
    template = repo.get_template(lang)
    assert template.language == lang
    assert template.filename
    assert len(template.code) > 0


def test_case_insensitive(repo):
    """Language identifiers are case-insensitive."""
    t1 = repo.get_template("python")
    t2 = repo.get_template("PYTHON")
    t3 = repo.get_template("Python")
    assert t1.code == t2.code == t3.code


def test_unsupported_language_raises(repo):
    with pytest.raises(UnsupportedLanguageError):
        repo.get_template("brainfuck")


def test_list_supported_languages(repo):
    langs = repo.list_supported_languages()
    assert "python" in langs
    assert "java" in langs
    assert len(langs) == len(SUPPORTED_LANGUAGES)
