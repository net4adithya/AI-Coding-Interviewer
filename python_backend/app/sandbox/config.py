"""Sandbox execution settings (Docker + Redis)."""

import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class SandboxSettings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    EXECUTION_QUEUE_KEY: str = "sandbox:execution:jobs"
    EXECUTION_RESULT_PREFIX: str = "sandbox:execution:result:"
    EXECUTION_RESULT_TTL_SEC: int = 600
    JOB_WAIT_TIMEOUT_SEC: float = 45.0

    EXECUTION_TIMEOUT_SEC: float = 10.0
    EXECUTION_MEMORY_MB: int = 256
    EXECUTION_CPUS: float = 1.0
    MAX_SOURCE_CODE_BYTES: int = 500 * 1024
    MAX_STDIN_BYTES: int = 64 * 1024
    MAX_OUTPUT_BYTES: int = 64 * 1024

    SANDBOX_ENABLED: bool = True

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"),
        env_file_encoding="utf-8",
        extra="allow",
    )

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


sandbox_settings = SandboxSettings()
