# python_backend/app/assessment/parsers/__init__.py
from .base import BaseQuestionBankParser
from .docx_parser import DocxQuestionBankParser

__all__ = [
    "BaseQuestionBankParser",
    "DocxQuestionBankParser",
]
