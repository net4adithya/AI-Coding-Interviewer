from typing import Dict, Any
from ..interfaces.analyzer_interface import BaseAnalyzer
from ..schemas.static_analysis import StaticAnalysisResponse

class PythonAnalyzer(BaseAnalyzer):
    """Placeholder Python analyzer.
    A real implementation would invoke Ruff, Radon, and Pylint to compute the metrics.
    For now we return deterministic mock values suitable for testing.
    """

    def supported_language(self) -> str:
        return "python"

    def analyzer_name(self) -> str:
        return "MockPythonAnalyzer"

    def analyzer_version(self) -> str:
        return "1.0.0"

    def health_check(self) -> bool:
        # In a real implementation, verify that the external tools are installed.
        return True

    def analyze(self, source_code: str) -> Dict[str, Any]:
        # Simple static calculations for demonstration purposes.
        lines = source_code.splitlines()
        loc = len(lines)
        blank = sum(1 for l in lines if not l.strip())
        comment = sum(1 for l in lines if l.strip().startswith('#'))
        comment_ratio = comment / loc if loc else 0
        # Mock complex metrics.
        return {
            "lines_of_code": loc,
            "blank_lines": blank,
            "comment_lines": comment,
            "comment_ratio": comment_ratio,
            "cyclomatic_complexity": 5,
            "cognitive_complexity": 3,
            "maintainability_index": 85.0,
            "duplicate_lines": 0,
            "duplicate_percentage": 0.0,
            "function_count": source_code.count('def '),
            "class_count": source_code.count('class '),
            "variable_count": source_code.count('=') - source_code.count('=='),
            "maximum_nesting_depth": 2,
            "security_warning_count": 0,
            "style_violation_count": 0,
            "code_smell_count": 0,
            "structured_output": {},
            "analyzer_name": self.analyzer_name(),
            "analyzer_version": self.analyzer_version(),
        }
