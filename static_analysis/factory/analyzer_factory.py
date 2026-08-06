from typing import Dict, Type
from ..interfaces.analyzer_interface import BaseAnalyzer
from ..exceptions import UnsupportedLanguageException

from ..analyzers.python_analyzer import PythonAnalyzer
from ..analyzers.java_analyzer import JavaAnalyzer
from ..analyzers.javascript_analyzer import JavaScriptAnalyzer
from ..analyzers.typescript_analyzer import TypeScriptAnalyzer
from ..analyzers.c_analyzer import CAnalyzer
from ..analyzers.cpp_analyzer import CppAnalyzer
from ..analyzers.csharp_analyzer import CSharpAnalyzer
from ..analyzers.go_analyzer import GoAnalyzer
from ..analyzers.rust_analyzer import RustAnalyzer
from ..analyzers.php_analyzer import PhpAnalyzer
from ..analyzers.kotlin_analyzer import KotlinAnalyzer
from ..analyzers.swift_analyzer import SwiftAnalyzer

class AnalyzerFactory:
    """Factory that returns a concrete analyzer instance based on language.
    The mapping is kept in a class-level registry so adding a new language only
    requires updating this dict (or dynamically registering at runtime via register()).
    """

    _registry: Dict[str, Type[BaseAnalyzer]] = {
        "python": PythonAnalyzer,
        "java": JavaAnalyzer,
        "javascript": JavaScriptAnalyzer,
        "typescript": TypeScriptAnalyzer,
        "c": CAnalyzer,
        "cpp": CppAnalyzer,
        "csharp": CSharpAnalyzer,
        "go": GoAnalyzer,
        "rust": RustAnalyzer,
        "php": PhpAnalyzer,
        "kotlin": KotlinAnalyzer,
        "swift": SwiftAnalyzer,
    }

    @classmethod
    def register(cls, language: str, analyzer_cls: Type[BaseAnalyzer]) -> None:
        """Dynamically register a new language analyzer class."""
        cls._registry[language.lower()] = analyzer_cls

    @classmethod
    def get_analyzer(cls, language: str) -> BaseAnalyzer:
        """Return an instantiated analyzer for *language*.
        Raises ``UnsupportedLanguageException`` if the language is not registered.
        """
        key = language.lower()
        analyzer_cls = cls._registry.get(key)
        if not analyzer_cls:
            raise UnsupportedLanguageException(language=language)
        return analyzer_cls()
