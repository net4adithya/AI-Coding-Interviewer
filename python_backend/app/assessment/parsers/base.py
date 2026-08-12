# python_backend/app/assessment/parsers/base.py
import abc
from typing import BinaryIO
from app.assessment.schemas.question import QuestionBankParseResult

class BaseQuestionBankParser(abc.ABC):
    """Abstract base class for question bank parsers."""
    
    @abc.abstractmethod
    def parse(self, file_stream: BinaryIO) -> QuestionBankParseResult:
        """
        Parse a file stream into a structured QuestionBankParseResult.
        
        Args:
            file_stream: Binary IO stream of the uploaded file.
            
        Returns:
            QuestionBankParseResult containing parsed questions and any non-fatal errors.
        """
        pass
