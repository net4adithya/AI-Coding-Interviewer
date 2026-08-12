# python_backend/app/execution/providers/factory.py
"""Execution provider factory."""

from app.execution.providers.base import BaseExecutionProvider
from app.execution.providers.judge0_provider import Judge0ExecutionProvider


def get_execution_provider() -> BaseExecutionProvider:
    """Factory function returning the configured BaseExecutionProvider.

    Currently returns Judge0ExecutionProvider.  Can be swapped or configured via
    environment variables without modifying service logic.
    """
    return Judge0ExecutionProvider()
