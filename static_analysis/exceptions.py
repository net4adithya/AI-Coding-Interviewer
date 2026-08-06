from fastapi import HTTPException, status

class AnalyzerNotFoundException(HTTPException):
    def __init__(self, analyzer_name: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND,
                         detail=f"Analyzer {analyzer_name} not found")

class UnsupportedLanguageException(HTTPException):
    def __init__(self, language: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST,
                         detail=f"Language '{language}' is not supported for static analysis")

class AnalysisFailedException(HTTPException):
    def __init__(self, reason: str):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY,
                         detail=f"Static analysis failed: {reason}")

class DuplicateAnalysisException(HTTPException):
    def __init__(self, submission_id: int):
        super().__init__(status_code=status.HTTP_409_CONFLICT,
                         detail=f"Static analysis already exists for submission {submission_id}")
