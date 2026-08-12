# python_backend/app/execution/config.py
"""Execution module settings loaded from environment or defaults.

Never log raw instances containing JUDGE0_API_KEY.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class ExecutionSettings(BaseSettings):
    # Judge0 Provider Settings
    JUDGE0_API_URL: str = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY: str = ""
    JUDGE0_REQUEST_TIMEOUT: float = 30.0
    JUDGE0_POLL_INTERVAL: float = 1.0
    JUDGE0_MAX_POLL_ATTEMPTS: int = 30
    JUDGE0_ENABLE_CALLBACK: bool = False

    # Configurable Execution Limits
    MAX_SOURCE_CODE_SIZE: int = 500 * 1024  # 500 KB
    MAX_TEST_CASES_PER_SUBMISSION: int = 50
    MAX_OUTPUT_SIZE: int = 64 * 1024  # 64 KB
    MAX_EXECUTION_TIME: float = 10.0  # 10 seconds per test case
    MAX_MEMORY_LIMIT: int = 512 * 1024  # 512 MB (in KB: 524288)

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"),
        env_file_encoding="utf-8",
        extra="allow",
    )

    def is_judge0_configured(self) -> bool:
        """Return True if Judge0 API URL is present."""
        return bool(self.JUDGE0_API_URL and self.JUDGE0_API_URL.strip())


execution_settings = ExecutionSettings()
