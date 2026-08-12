# python_backend/app/editor/exceptions.py
"""Domain-specific exceptions for the editor module."""

from fastapi import HTTPException, status


class DraftNotFoundException(HTTPException):
    def __init__(self, draft_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft with ID {draft_id} not found.",
        )


class DraftLockedError(HTTPException):
    def __init__(self, draft_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Draft {draft_id} is locked after submission and cannot be modified.",
        )


class DraftAccessDeniedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this draft.",
        )


class SubmissionAlreadyExistsError(HTTPException):
    def __init__(self, draft_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Draft {draft_id} has already been submitted.",
        )


class UnsupportedLanguageError(HTTPException):
    def __init__(self, language: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{language}' is not supported.",
        )


class CodeSizeTooLargeError(HTTPException):
    def __init__(self, size: int, max_size: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Code size {size} bytes exceeds the maximum allowed size of {max_size} bytes.",
        )


class AssignmentNotFoundException(HTTPException):
    def __init__(self, assignment_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment with ID {assignment_id} not found.",
        )


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "Authentication required."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class InternRoleRequiredError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires intern role.",
        )


class AuthorityRoleRequiredError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires authority role.",
        )
