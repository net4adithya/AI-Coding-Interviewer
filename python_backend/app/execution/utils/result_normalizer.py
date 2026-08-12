# python_backend/app/execution/utils/result_normalizer.py
"""Normalizes provider status IDs into application-level execution statuses.

Judge0 status IDs reference:
  1: In Queue
  2: Processing
  3: Accepted (PASSED)
  4: Wrong Answer
  5: Time Limit Exceeded
  6: Compilation Error
  7: Runtime Error (SIGSEGV)
  8: Runtime Error (SIGXFSZ)
  9: Runtime Error (FPE)
 10: Runtime Error (ABRT)
 11: Runtime Error (NZEC)
 12: Runtime Error (Other)
 13: Internal Error
 14: Exec Format Error
"""

import enum
from typing import Tuple


class ExecutionStatusEnum(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    PASSED = "PASSED"
    WRONG_ANSWER = "WRONG_ANSWER"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Map Judge0 status ID -> (ExecutionStatusEnum, passed: bool, description: str)
_STATUS_MAP = {
    1: (ExecutionStatusEnum.QUEUED, False, "In Queue"),
    2: (ExecutionStatusEnum.PROCESSING, False, "Processing"),
    3: (ExecutionStatusEnum.PASSED, True, "Passed"),
    4: (ExecutionStatusEnum.WRONG_ANSWER, False, "Wrong Answer"),
    5: (ExecutionStatusEnum.TIME_LIMIT_EXCEEDED, False, "Time Limit Exceeded"),
    6: (ExecutionStatusEnum.COMPILATION_ERROR, False, "Compilation Error"),
    7: (ExecutionStatusEnum.RUNTIME_ERROR, False, "Runtime Error (SIGSEGV)"),
    8: (ExecutionStatusEnum.RUNTIME_ERROR, False, "Runtime Error (SIGXFSZ)"),
    9: (ExecutionStatusEnum.RUNTIME_ERROR, False, "Runtime Error (FPE)"),
    10: (ExecutionStatusEnum.RUNTIME_ERROR, False, "Runtime Error (ABRT)"),
    11: (ExecutionStatusEnum.RUNTIME_ERROR, False, "Runtime Error (NZEC)"),
    12: (ExecutionStatusEnum.RUNTIME_ERROR, False, "Runtime Error"),
    13: (ExecutionStatusEnum.INTERNAL_ERROR, False, "Internal Error"),
    14: (ExecutionStatusEnum.SYSTEM_ERROR, False, "Exec Format Error"),
}


def normalize_judge0_status(status_id: int) -> Tuple[ExecutionStatusEnum, bool, str]:
    """Convert a numeric Judge0 status ID into an internal status enum, pass flag, and message.

    Args:
        status_id: Judge0 status ID integer.

    Returns:
        Tuple of (ExecutionStatusEnum, passed_bool, description_str).
    """
    if status_id in _STATUS_MAP:
        return _STATUS_MAP[status_id]

    return (ExecutionStatusEnum.INTERNAL_ERROR, False, f"Unknown Judge0 Status ({status_id})")
