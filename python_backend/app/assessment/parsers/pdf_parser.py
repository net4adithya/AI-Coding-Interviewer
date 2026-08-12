import re
from typing import BinaryIO, Dict, Any, List
try:
    from pypdf import PdfReader
except ImportError:
    pass

from app.assessment.parsers.base import BaseQuestionBankParser
from app.assessment.schemas.question import QuestionBankParseResult, ParsedQuestionSchema

class PdfQuestionBankParser(BaseQuestionBankParser):
    """
    Parses a PDF file containing coding questions using heuristics.
    """
    
    def parse(self, file_stream: BinaryIO) -> QuestionBankParseResult:
        result = QuestionBankParseResult()
        try:
            reader = PdfReader(file_stream)
            text_lines = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_lines.extend(text.split("\n"))
        except Exception as e:
            result.errors.append(f"Upload Error: Failed to read PDF. It might be corrupted or unreadable. Details: {str(e)}")
            return result
            
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
                
            if ":" in text and len(text.split("\n")) == 1:
                prefix = text.split(":", 1)[0].lower().strip()
                if prefix in ["topic", "difficulty", "time", "suggested time", "language"]:
                    text = text.split(":", 1)[1].strip()

            sec = current_section.lower()
            if "title" in sec:
                if "title" not in current_question:
                    current_question["title"] = text
            elif "topic" in sec:
                current_question["topic"] = text
            elif "difficulty" in sec:
                current_question["difficulty"] = text.upper()
            elif "problem" in sec or "statement" in sec:
                current_question["problem_statement"] = current_question.get("problem_statement", "") + "\n\n" + text if current_question.get("problem_statement") else text
            elif "constraint" in sec:
                current_question["constraints"] = text
            elif "input" in sec:
                current_question["problem_statement"] = current_question.get("problem_statement", "") + "\n\nInput:\n" + text
            elif "output" in sec:
                current_question["problem_statement"] = current_question.get("problem_statement", "") + "\n\nOutput:\n" + text
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
            
            current_text.clear()

        def save_question():
            nonlocal current_question, current_section
            save_section()
            if not current_question:
                return
                
            # If the title is just a document header like "Question Bank", skip it or rename it
            title = current_question.get("title", "")
            if not title or "question bank" in title.lower():
                # Not a real question, discard
                current_question.clear()
                current_section = None
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

        is_first_question = True
        
        for line in text_lines:
            text = line.strip()
            if not text:
                continue
            
            # Skip document headers
            if is_first_question and "question bank" in text.lower():
                continue
                
            # Detect Question Boundary
            is_question_boundary = (
                text.lower().startswith("question:") or 
                re.match(r'^question\s+\d+', text.lower()) or
                text.lower().startswith("title:")
            )
            
            if is_question_boundary:
                save_question()
                is_first_question = False
                current_section = "Title"
                if ":" in text:
                    parts = text.split(":", 1)
                    if len(parts) > 1 and parts[1].strip():
                        current_text.append(parts[1].strip())
                continue
                
            # Detect section boundaries
            is_section_boundary = (
                (len(text) < 50 and text.endswith(':')) or
                re.match(r'^(Topic|Difficulty|Time|Suggested Time|Language|Input|Output|Constraints?|Examples?|Problem|Statement|Expected Concepts)s?\s*:', text, re.IGNORECASE)
            )
            
            # If we are inside an example, ignore "Input:" and "Output:" as global section boundaries
            if current_section and current_section.lower().startswith("example"):
                if re.match(r'^(Input|Output)\s*:', text, re.IGNORECASE):
                    is_section_boundary = False
            
            if is_section_boundary:
                save_section()
                if ":" in text and not text.endswith(":"):
                    current_section = text.split(":")[0].strip()
                    current_text.append(text)
                else:
                    current_section = text.replace(':', '').strip()
            else:
                # Fallback: if we haven't started a section yet, it's the title
                if not current_section:
                    current_section = "Title"
                    current_text.append(text)
                elif current_section == "Title" and len(current_text) >= 1:
                    save_section()
                    current_section = "Problem Statement"
                    current_text.append(text)
                else:
                    current_text.append(text)
        
        save_question()
        
        if not result.questions:
            result.errors.append("Validation Error: No valid questions could be extracted from this PDF. Please ensure the document is formatted correctly.")
            
        return result
