"""Sandbox execution request/response contracts (Judge0-independent)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ExecutionRequest(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=128)
    language: str = Field(..., min_length=1, max_length=32)
    source_code: str = Field(..., min_length=1)
    stdin: str = ""


class ExecutionResponse(BaseModel):
    job_id: Optional[str] = None
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time_ms: int = 0
    memory_kb: int = 0
