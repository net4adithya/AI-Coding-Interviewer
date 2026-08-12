# python_backend/app/assessment/parsers/docx_parser.py
import re
from typing import BinaryIO, Dict, Any, List
from docx import Document

from app.assessment.parsers.base import BaseQuestionBankParser
from app.assessment.schemas.question import QuestionBankParseResult, ParsedQuestionSchema

class DocxQuestionBankParser(BaseQuestionBankParser):
    """
    Parses a DOCX file containing coding questions using heuristics.
    Tries to identify questions by "Heading 1" or lines starting with "Question".
    Identifies sections based on Headings or lines ending with colons.
    """
    
    def parse(self, file_stream: BinaryIO) -> QuestionBankParseResult:
        try:
            doc = Document(file_stream)
        except Exception as e:
            return QuestionBankParseResult(errors=[f"Failed to load DOCX: {str(e)}"])
        
        result = QuestionBankParseResult()
        
        current_question: Dict[str, Any] = {}
        current_section = None
        current_text = []

        def save_section():
            nonlocal current_section, current_text, current_question
            if not current_section or not current_text:
                return
            
            text = "\n".join(current_text).strip()
            if not text:
                return
                
            # If text is like "Topic: Arrays", strip the prefix
            if ":" in text and len(text.split("\n")) == 1:
                prefix = text.split(":", 1)[0].lower().strip()
                if prefix in ["topic", "difficulty", "time", "language"]:
                    text = text.split(":", 1)[1].strip()

            sec = current_section.lower()
            if "title" in sec or "question" in sec:
                if "title" not in current_question:
                    current_question["title"] = text
            elif "topic" in sec:
                current_question["topic"] = text
            elif "difficulty" in sec:
                current_question["difficulty"] = text.upper()
            elif "problem" in sec or "statement" in sec:
                current_question["problem_statement"] = text
            elif "constraint" in sec:
                current_question["constraints"] = text
            elif "time" in sec:
                match = re.search(r'\d+', text)
                if match:
                    current_question["expected_time_minutes"] = int(match.group())
            elif "language" in sec:
                current_question["programming_languages"] = [l.strip().lower() for l in text.split(",")]
            elif "example" in sec:
                if "examples" not in current_question:
                    current_question["examples"] = []
                current_question["examples"].append({"description": text})
            elif "starter code" in sec:
                if "starter_code" not in current_question:
                    current_question["starter_code"] = {}
                current_question["starter_code"]["default"] = text
            elif "test case" in sec:
                if "test_cases" not in current_question:
                    current_question["test_cases"] = []
                current_question["test_cases"].append({
                    "stdin": text, 
                    "expected_output": "",
                    "is_hidden": False,
                    "weight": 1.0,
                    "time_limit_sec": 10.0,
                    "memory_limit_mb": 512
                })
            
            current_text.clear()

        def save_question():
            nonlocal current_question, current_section
            save_section()
            if not current_question:
                return
            
            try:
                # Add default fields if missing to ensure validation passes for malformed questions
                if "title" not in current_question:
                    current_question["title"] = "Untitled Question"
                if "problem_statement" not in current_question:
                    current_question["problem_statement"] = "No problem statement provided."
                if "topic" not in current_question:
                    current_question["topic"] = "General"
                
                diff = current_question.get("difficulty", "MEDIUM")
                if diff not in ["EASY", "MEDIUM", "HARD"]:
                    diff = "MEDIUM"
                current_question["difficulty"] = diff

                q = ParsedQuestionSchema(**current_question)
                result.questions.append(q)
            except Exception as e:
                result.errors.append(f"Failed to parse a question: {str(e)}")
            
            current_question.clear()
            current_section = None

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # Detect Question Boundary
            is_question_boundary = (
                para.style.name.startswith('Heading 1') or 
                text.lower().startswith("question:") or 
                re.match(r'^question\s+\d+', text.lower())
            )
            
            if is_question_boundary:
                save_question()
                current_section = "Title"
                if text.lower().startswith("question:"):
                    current_text.append(text.split(":", 1)[1].strip())
                elif re.match(r'^question\s+\d+:', text.lower()):
                    current_text.append(text.split(":", 1)[1].strip())
                else:
                    current_text.append(text)
                continue
                
            # Detect section boundaries
            is_section_boundary = (
                para.style.name.startswith('Heading') or 
                (len(text) < 50 and text.endswith(':')) or
                re.match(r'^(Topic|Difficulty|Time|Language)s?\s*:', text, re.IGNORECASE)
            )
            
            if is_section_boundary:
                save_section()
                if ":" in text and not text.endswith(":"):
                    # Inline key-value like "Topic: Arrays"
                    current_section = text.split(":")[0].strip()
                    current_text.append(text)
                else:
                    current_section = text.replace(':', '').strip()
            else:
                if current_section:
                    current_text.append(text)
                else:
                    current_section = "Problem Statement"
                    current_text.append(text)
        
        save_question()
        
        if not result.questions and not result.errors:
            result.errors.append("No questions found in the document.")
            
        return result
