# python_backend/app/execution/exceptions.py
"""Controlled domain exceptions for the code execution engine.

Maps domain errors to standardized HTTP status codes and safe error messages.
"""

from fastapi import HTTPException, status


class ExecutionEngineException(HTTPException):
    """Base exception for execution engine errors."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class SubmissionNotFoundException(ExecutionEngineException):
    def __init__(self, submission_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found.",
        )


class SubmissionNotFinalizedException(ExecutionEngineException):
    def __init__(self, submission_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Submission {submission_id} is not finalized or ready for execution.",
        )


class UnsupportedLanguageException(ExecutionEngineException):
    def __init__(self, language: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{language}' is not supported by the execution engine.",
        )


class ExecutionProviderUnavailableError(ExecutionEngineException):
    def __init__(self, provider: str = "Judge0", reason: str = "Provider unreachable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Execution provider '{provider}' is currently unavailable: {reason}",
        )


class ExecutionTimeoutError(ExecutionEngineException):
    def __init__(self, timeout_sec: float):
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Execution timed out after {timeout_sec} seconds.",
        )


class ExecutionRateLimitedError(ExecutionEngineException):
    def __init__(self, provider: str = "Judge0"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Execution provider '{provider}' rate limit exceeded. Please try again later.",
        )


class DuplicateExecutionException(ExecutionEngineException):
    def __init__(self, submission_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Submission {submission_id} is already being executed or completed.",
        )


class ExecutionConfigurationError(ExecutionEngineException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution engine configuration error: {detail}",
        )


class TestCaseNotFoundException(ExecutionEngineException):
    def __init__(self, assignment_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No test cases found for assignment {assignment_id}.",
        )


class ExecutionAccessDeniedError(ExecutionEngineException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to execution results.",
        )


class CodeSizeLimitExceededException(ExecutionEngineException):
    def __init__(self, size: int, limit: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Source code size ({size} bytes) exceeds limit of {limit} bytes.",
        )
