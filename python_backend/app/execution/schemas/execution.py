# python_backend/app/execution/schemas/execution.py
"""Pydantic schemas for execution API requests and responses."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExecutionStartResponse(BaseModel):
    submission_id: int
    status: str = "PROCESSING"
    message: str = "Execution pipeline triggered asynchronously."

    model_config = ConfigDict(from_attributes=True)


class ExecutionTestCaseResultResponse(BaseModel):
    id: int
    submission_id: int
    test_case_id: int
    provider: str
    language: str
    status: str
    passed: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    message: Optional[str] = None
    execution_time: Optional[float] = None
    memory: Optional[int] = None
    
    # Optional fields – filtered out for interns if test case is hidden
    stdin: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    is_hidden: bool = False

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionSummaryResponse(BaseModel):
    submission_id: int
    status: str
    total_test_cases: int
    passed_test_cases: int
    failed_test_cases: int
    pass_percentage: float
    max_execution_time: float
    avg_execution_time: float
    max_memory: int
    avg_memory: float
    compilation_success: bool
    results: List[ExecutionTestCaseResultResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ExecutionStatusResponse(BaseModel):
    submission_id: int
    status: str
    completed: bool

    model_config = ConfigDict(from_attributes=True)


class ExecutionHealthResponse(BaseModel):
    provider: str
    configured: bool
    available: bool
    version: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExecutionResultResponse(BaseModel):
    id: int
    submission_id: int
    test_case_id: int
    provider: str
    language: str
    judge0_token: Optional[str] = None
    status: str
    status_id: Optional[int] = None
    passed: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    message: Optional[str] = None
    execution_time: Optional[float] = None
    memory: Optional[int] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
