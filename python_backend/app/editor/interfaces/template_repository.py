# python_backend/app/editor/interfaces/template_repository.py
"""Abstract interface for template repositories.

Implementations must read starter templates for a given language.
All concrete implementations must be registered as a TemplateRepositoryInterface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Template:
    """Holds the content of a starter template for a given language."""

    language: str
    filename: str
    code: str


class TemplateRepositoryInterface(ABC):
    """Abstract base class for template repositories."""

    @abstractmethod
    def get_template(self, language: str) -> Template:
        """Retrieve the starter template for the given language.

        Args:
            language: Programming language identifier (case-insensitive).

        Returns:
            Template dataclass instance.

        Raises:
            UnsupportedLanguageError: If the language is not supported.
        """
        ...

    @abstractmethod
    def list_supported_languages(self) -> list[str]:
        """Return the list of all supported language identifiers (lowercase)."""
        ...
