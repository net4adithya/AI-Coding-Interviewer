# python_backend/app/assessment/services/question_bank_service.py
from typing import BinaryIO, List
from sqlalchemy.orm import Session

from app.assessment.models.assessment import QuestionBank, Question, DifficultyEnum
from app.assessment.repositories.question_bank_repository import QuestionBankRepository
from app.assessment.parsers.base import BaseQuestionBankParser
from app.assessment.schemas.question_bank import QuestionBankDetailResponse

class QuestionBankService:
    def __init__(self, db: Session, parser: BaseQuestionBankParser):
        self.repo = QuestionBankRepository(db)
        self.parser = parser

    def upload_and_parse(self, owner_id: int, filename: str, file_stream: BinaryIO) -> QuestionBankDetailResponse:
        print(f"=== UPLOAD_AND_PARSE DIAGNOSTIC ===")
        print(f"File being processed: {filename}")
        
        # 1. Parse document
        try:
            parse_result = self.parser.parse(file_stream)
            print(f"Parser returned successfully. Questions extracted: {len(parse_result.questions)}")
            if parse_result.errors:
                print(f"Parser encountered errors: {parse_result.errors}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Exception during parse: {str(e)}")
            raise

        if not parse_result.questions:
            error_msg = "; ".join(parse_result.errors) if parse_result.errors else "No valid questions found."
            print(f"Failing because no questions found: {error_msg}")
            raise ValueError(error_msg)
            
        # 2. Create QuestionBank record
        bank = QuestionBank(
            owner_id=owner_id,
            filename=filename,
            status="PROCESSING"
        )
        self.repo.create(bank)
        
        # 3. Save Questions
        db_questions = []
        for q_schema in parse_result.questions:
            # Map enum correctly
            diff_enum = DifficultyEnum(q_schema.difficulty)
            
            # Note: We are no longer saving test_cases into JSONB.
            # We will handle test cases via the dedicated TestCase model separately if needed,
            # or for Phase 9, if the parser returns test cases, we need to create TestCase rows.
            # Let's save the basic Question first.
            
            q = Question(
                question_bank_id=bank.id,
                title=q_schema.title,
                problem_statement=q_schema.problem_statement,
                topic=q_schema.topic,
                difficulty=diff_enum,
                constraints=q_schema.constraints,
                examples=q_schema.examples,
                expected_time_minutes=q_schema.expected_time_minutes,
                programming_languages=q_schema.programming_languages,
                starter_code=q_schema.starter_code
            )
            db_questions.append(q)
            
        self.repo.create_questions(db_questions)
        
        # 4. Now that Questions have IDs, we need to create TestCase records for them.
        # But wait, QuestionBankService doesn't have access to the TestCase repository easily here
        # without circular imports. We can just use the db session directly.
        if parse_result.questions:
            from app.execution.models.test_case import TestCase
            test_cases_to_create = []
            for q_schema, db_question in zip(parse_result.questions, db_questions):
                for tc in q_schema.test_cases:
                    new_tc = TestCase(
                        question_id=db_question.id,
                        assignment_id=None, # Nullable now
                        stdin=tc.get("stdin", ""),
                        expected_output=tc.get("expected_output", ""),
                        is_hidden=tc.get("is_hidden", False),
                        weight=tc.get("weight", 1.0),
                        time_limit_sec=tc.get("time_limit_sec", 10.0),
                        memory_limit_mb=tc.get("memory_limit_mb", 512)
                    )
                    test_cases_to_create.append(new_tc)
            
            if test_cases_to_create:
                self.repo.db.add_all(test_cases_to_create)
                self.repo.db.commit()
        
        # 5. Update Bank status
        bank.status = "COMPLETED" if parse_result.questions else "FAILED"
        bank.question_count = len(db_questions)
        bank.parsing_errors = parse_result.errors
        
        self.repo.db.commit()
        self.repo.db.refresh(bank)
        
        return QuestionBankDetailResponse(
            id=bank.id,
            owner_id=bank.owner_id,
            filename=bank.filename,
            status=bank.status,
            question_count=bank.question_count,
            created_at=bank.created_at,
            parsing_errors=bank.parsing_errors,
            questions=parse_result.questions
        )

    def get_all(self) -> List[QuestionBank]:
        return self.repo.get_all()

    def get_by_id(self, bank_id: int) -> QuestionBank:
        return self.repo.get_by_id(bank_id)

    def get_questions(self, bank_id: int) -> List[Question]:
        return self.repo.get_questions_for_bank(bank_id)
