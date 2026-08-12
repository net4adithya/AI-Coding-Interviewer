# python_backend/app/assessment/schemas/question.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ParsedQuestionSchema(BaseModel):
    title: str = Field(..., description="Title of the question")
    problem_statement: str = Field(..., description="Problem description")
    topic: str = Field(..., description="Topic category e.g., Arrays")
    difficulty: str = Field(..., description="EASY, MEDIUM, or HARD")
    constraints: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None
    expected_time_minutes: Optional[int] = None
    programming_languages: List[str] = Field(default_factory=list)
    starter_code: Optional[Dict[str, str]] = None
    test_cases: List[Dict[str, Any]] = Field(default_factory=list, description="List of test cases {stdin, expected_output, is_hidden, weight, time_limit_sec, memory_limit_mb}")

class QuestionBankParseResult(BaseModel):
    questions: List[ParsedQuestionSchema] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
