from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, source_code: str) -> Dict[str, Any]:
        """Analyze the given source code and return a dictionary with all metric keys.
        The dict must contain every field defined in the StaticAnalysis model plus a
        ``structured_output`` key for language‑specific findings.
        """
        raise NotImplementedError

    @abstractmethod
    def supported_language(self) -> str:
        """Return the language identifier (e.g., ``python``)."""
        raise NotImplementedError

    @abstractmethod
    def analyzer_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def analyzer_version(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        """Return ``True`` if the underlying toolchain is available."""
        raise NotImplementedError
