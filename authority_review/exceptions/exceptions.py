class AuthorityReviewException(Exception):
    """Base exception for authority review module."""
    pass

class AuthorityReviewNotFoundException(AuthorityReviewException):
    def __init__(self, submission_id: int = None, review_id: int = None):
        if submission_id:
            self.message = f"Authority review for submission ID {submission_id} not found"
        elif review_id:
            self.message = f"Authority review with ID {review_id} not found"
        else:
            self.message = "Authority review record not found"
        super().__init__(self.message)

class SubmissionNotFoundException(AuthorityReviewException):
    def __init__(self, submission_id: int):
        self.message = f"Submission with ID {submission_id} not found"
        super().__init__(self.message)

class UnauthorizedReviewException(AuthorityReviewException):
    def __init__(self, role: str = None):
        self.message = f"User with role '{role}' is not authorized to access or perform Authority Reviews" if role else "Unauthorized access to Authority Review"
        super().__init__(self.message)

class DuplicateAuthorityReviewException(AuthorityReviewException):
    def __init__(self, submission_id: int):
        self.message = f"Authority review already exists for submission ID {submission_id}"
        super().__init__(self.message)
