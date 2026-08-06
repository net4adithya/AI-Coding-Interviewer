import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from static_analysis.factory.analyzer_factory import AnalyzerFactory
from static_analysis.interfaces.analyzer_interface import BaseAnalyzer
from static_analysis.exceptions import UnsupportedLanguageException

def test_factory_returns_analyzers_for_all_supported_languages():
    languages = [
        "python", "java", "javascript", "typescript",
        "c", "cpp", "csharp", "go", "rust",
        "php", "kotlin", "swift"
    ]
    for lang in languages:
        analyzer = AnalyzerFactory.get_analyzer(lang)
        assert isinstance(analyzer, BaseAnalyzer)
        assert analyzer.supported_language().lower() == lang
        assert analyzer.health_check() is True
        result = analyzer.analyze("x = 1\n")
        assert "lines_of_code" in result
        assert "analyzer_name" in result

def test_factory_raises_unsupported_language_exception():
    with pytest.raises(UnsupportedLanguageException):
        AnalyzerFactory.get_analyzer("unsupported_lang_xyz")

def test_factory_dynamic_registration():
    class CustomAnalyzer(BaseAnalyzer):
        def supported_language(self) -> str:
            return "custom"
        def analyzer_name(self) -> str:
            return "CustomAnalyzer"
        def analyzer_version(self) -> str:
            return "1.0.0"
        def health_check(self) -> bool:
            return True
        def analyze(self, source_code: str):
            return {"lines_of_code": 10, "analyzer_name": "CustomAnalyzer"}

    AnalyzerFactory.register("custom", CustomAnalyzer)
    analyzer = AnalyzerFactory.get_analyzer("custom")
    assert isinstance(analyzer, CustomAnalyzer)
    assert analyzer.analyze("")["lines_of_code"] == 10
