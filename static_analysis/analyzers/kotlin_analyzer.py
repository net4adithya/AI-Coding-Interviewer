from typing import Dict, Any
from ..interfaces.analyzer_interface import BaseAnalyzer

class KotlinAnalyzer(BaseAnalyzer):
    """Mock Kotlin analyzer returning deterministic metrics for testing."""

    def supported_language(self) -> str:
        return "kotlin"

    def analyzer_name(self) -> str:
        return "MockKotlinAnalyzer"

    def analyzer_version(self) -> str:
        return "1.0.0"

    def health_check(self) -> bool:
        return True

    def analyze(self, source_code: str) -> Dict[str, Any]:
        lines = source_code.splitlines()
        loc = len(lines)
        blank = sum(1 for l in lines if not l.strip())
        comment = sum(1 for l in lines if l.strip().startswith('//') or l.strip().startswith('/*'))
        comment_ratio = comment / loc if loc else 0
        return {
            "lines_of_code": loc,
            "blank_lines": blank,
            "comment_lines": comment,
            "comment_ratio": comment_ratio,
            "cyclomatic_complexity": 4,
            "cognitive_complexity": 2,
            "maintainability_index": 82.0,
            "duplicate_lines": 0,
            "duplicate_percentage": 0.0,
            "function_count": source_code.count('fun '),
            "class_count": source_code.count('class '),
            "variable_count": source_code.count('val ') + source_code.count('var '),
            "maximum_nesting_depth": 2,
            "security_warning_count": 0,
            "style_violation_count": 0,
            "code_smell_count": 0,
            "structured_output": {},
            "analyzer_name": self.analyzer_name(),
            "analyzer_version": self.analyzer_version(),
        }
