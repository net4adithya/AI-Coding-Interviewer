# python_backend/app/execution/providers/base.py
"""Abstract base class and data structures for code execution providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ExecutionRequest:
    """Internal provider-agnostic request structure for remote execution."""
    submission_id: int
    test_case_id: int
    language: str
    source_code: str
    stdin: str = ""
    expected_output: str = ""
    time_limit_sec: float = 10.0
    memory_limit_mb: int = 512


@dataclass
class ExecutionRawResult:
    """Internal provider-agnostic raw response structure returned by execution providers."""
    token: str
    status_id: int
    status_description: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    message: Optional[str] = None
    execution_time: Optional[float] = None  # in seconds
    memory: Optional[int] = None  # in KB
    raw_payload: Optional[Dict[str, Any]] = None


class BaseExecutionProvider(ABC):
    """Abstract interface that all remote execution providers must implement.

    Ensures the business logic in ExecutionService never directly imports or relies
    on provider-specific APIs (such as Judge0 API keys, endpoints, or response formats).
    """

    @abstractmethod
    async def submit(self, request: ExecutionRequest) -> str:
        """Submit code to remote provider and return an execution tracking token."""
        pass

    @abstractmethod
    async def get_result(self, token: str) -> ExecutionRawResult:
        """Fetch current execution result status for a token."""
        pass

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionRawResult:
        """Submit source code and poll until completion or timeout."""
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g. 'judge0')."""
        pass

    @abstractmethod
    def provider_version(self) -> str:
        """Return provider version string."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform provider health check."""
        pass
