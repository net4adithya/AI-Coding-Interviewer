# python_backend/app/demo/router.py
"""
FastAPI router for DEMO MODE endpoints.

All endpoints are mounted at /demo/* when DEMO_MODE=true.
No PostgreSQL or Supabase required.

Authentication:
  POST /demo/auth/login returns a token like "base64(email:role)"
  Subsequent requests include X-Demo-Token header.
  get_demo_user() dependency extracts email/role from this header.
"""

import asyncio
import base64
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.demo.demo_store import DemoStore
from app.demo import gemini_service, judge0_service

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Demo credentials (hardcoded for presentation)
# ---------------------------------------------------------------------------
DEMO_USERS = {
    "admin@test.com": {"password": "demo123", "role": "authority", "name": "Admin"},
    "intern@test.com": {"password": "demo123", "role": "intern", "name": "Intern"},
}

DEMO_CANDIDATES = [
    {
        "id": "intern-001",
        "name": "Demo Intern",
        "email": "intern@test.com",
        "status": "Available",
        "assigned_assessment": None,
    }
]


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _make_token(email: str, role: str) -> str:
    raw = f"{email}:{role}"
    return base64.b64encode(raw.encode()).decode()


def _parse_token(token: str) -> Dict[str, str]:
    try:
        raw = base64.b64decode(token.encode()).decode()
        email, role = raw.split(":", 1)
        return {"email": email, "role": role}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid demo token.")


def get_demo_user(
    x_demo_token: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, str]:
    """Dependency: extract demo user from X-Demo-Token or Authorization header."""
    token = x_demo_token
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing demo auth token. Please log in first.",
        )
    return _parse_token(token)


def require_authority(user: Dict[str, str] = Depends(get_demo_user)) -> Dict[str, str]:
    if user["role"] not in ("authority", "admin"):
        raise HTTPException(status_code=403, detail="Authority role required.")
    return user


def require_intern(user: Dict[str, str] = Depends(get_demo_user)) -> Dict[str, str]:
    if user["role"] not in ("intern", "admin"):
        raise HTTPException(status_code=403, detail="Intern role required.")
    return user


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    email: str
    name: str


class GenerateQuestionsRequest(BaseModel):
    title: str
    description: str = ""
    duration_minutes: int = 60
    language: str = "Python"
    topic: str = "Algorithms"
    easy_count: int = 0
    medium_count: int = 0
    hard_count: int = 0


class ConfirmAssessmentRequest(BaseModel):
    title: str
    description: str = ""
    duration_minutes: int
    language: str
    topic: str
    easy_count: int
    medium_count: int
    hard_count: int
    questions: List[dict]   # confirmed/edited questions from frontend


class AssignRequest(BaseModel):
    assessment_id: str
    intern_email: str


class RunCodeRequest(BaseModel):
    source_code: str
    language: str
    stdin: str = ""


class RunTestCasesRequest(BaseModel):
    source_code: str
    language: str
    test_cases: List[dict]


class SubmitAssessmentRequest(BaseModel):
    assessment_id: str
    code_by_question: Dict[str, dict]   # question_id -> {language, code}
    final_language: str = "python"


class SaveDecisionRequest(BaseModel):
    decision: str   # "RECOMMENDED" | "NEEDS_REVIEW" | "NOT_RECOMMENDED"
    notes: str = ""


class ReviewSelectionRequest(BaseModel):
    title: str
    description: str = ""
    duration_minutes: int = 60
    language: str = "Python"
    topic: str = "Algorithms"
    selected_questions: List[dict]


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@router.post("/auth/login", response_model=LoginResponse)
async def demo_login(req: LoginRequest):
    """Authenticate demo user with hardcoded credentials."""
    user = DEMO_USERS.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid demo credentials. Use admin@test.com or intern@test.com with password 'demo123'.",
        )
    token = _make_token(req.email, user["role"])
    return LoginResponse(token=token, role=user["role"], email=req.email, name=user["name"])


@router.post("/auth/logout")
async def demo_logout():
    return {"message": "Logged out successfully."}


@router.get("/auth/me", response_model=LoginResponse)
async def demo_auth_me(user: Dict[str, str] = Depends(get_demo_user)):
    """Return logged in demo user info including role."""
    email = user["email"]
    role = user["role"]
    demo_user = DEMO_USERS.get(email, {})
    name = demo_user.get("name", email.split("@")[0])
    token = _make_token(email, role)
    return LoginResponse(token=token, role=role, email=email, name=name)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(require_authority)):
    return DemoStore.get_dashboard_stats()


# ---------------------------------------------------------------------------
# Question Banks (PDF Upload & Listing for DEMO MODE)
# ---------------------------------------------------------------------------

from fastapi import UploadFile, File

@router.post("/question-banks/upload")
async def upload_question_bank_pdf(
    file: UploadFile = File(...),
    user: dict = Depends(require_authority),
):
    """Parse PDF question bank and store in DemoStore."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        from app.assessment.parsers.pdf_parser import PdfQuestionBankParser
        contents = await file.read()
        import io
        stream = io.BytesIO(contents)
        parser = PdfQuestionBankParser()
        parse_result = parser.parse(stream)

        if parse_result.errors and not parse_result.questions:
            error_msg = "\n".join(parse_result.errors)
            raise HTTPException(status_code=400, detail=f"PDF Parse Error: {error_msg}")

        questions = []
        for idx, q in enumerate(parse_result.questions):
            questions.append({
                "id": f"q-pdf-{uuid.uuid4()}",
                "title": q.title or f"Question {idx+1}",
                "difficulty": q.difficulty.capitalize() if q.difficulty else "Medium",
                "topic": q.topic or "Algorithms",
                "problem_statement": q.problem_statement or "No problem statement provided.",
                "constraints": q.constraints or "N/A",
                "input_format": getattr(q, "input_format", "Standard input"),
                "output_format": getattr(q, "output_format", "Standard output"),
                "examples": [e.dict() if hasattr(e, 'dict') else e for e in (q.examples or [])],
                "test_cases": [t.dict() if hasattr(t, 'dict') else t for t in (q.test_cases or [])] or [
                    {"input": "1", "expected_output": "1", "is_hidden": False}
                ],
            })

        bank_title = file.filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
        bank_data = {
            "title": bank_title,
            "topic": questions[0]["topic"] if questions else "Algorithms",
            "description": f"Uploaded from {file.filename}",
            "questions": questions
        }
        saved_bank = DemoStore.save_question_bank(bank_data)
        return {
            "message": "Question Bank uploaded successfully.",
            "question_bank": saved_bank,
            "total_questions": len(questions)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[DemoRouter] Question bank PDF upload error")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@router.get("/question-banks")
async def list_question_banks(user: dict = Depends(require_authority)):
    return DemoStore.get_question_banks()


@router.get("/question-banks/{bank_id}")
async def get_question_bank_detail(bank_id: str, user: dict = Depends(require_authority)):
    bank = DemoStore.get_question_bank(bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Question Bank not found.")
    return bank


@router.post("/assessments/review-selection")
async def review_assessment_selection(
    req: ReviewSelectionRequest,
    user: dict = Depends(require_authority),
):
    """Call real Gemini to review and validate selected assessment questions from Question Bank."""
    res = await gemini_service.review_assessment_selection(
        title=req.title,
        description=req.description,
        duration_minutes=req.duration_minutes,
        language=req.language,
        topic=req.topic,
        selected_questions=req.selected_questions,
    )
    return res


# ---------------------------------------------------------------------------
# Assessment Generation
# ---------------------------------------------------------------------------

@router.post("/assessments/generate")
async def generate_assessment_questions(
    req: GenerateQuestionsRequest,
    user: dict = Depends(require_authority),
):
    """Call real Gemini to generate questions. Returns list of question dicts."""
    total = req.easy_count + req.medium_count + req.hard_count
    if total == 0:
        raise HTTPException(status_code=400, detail="Please specify at least one question (Easy, Medium, or Hard count > 0).")

    try:
        questions = await gemini_service.generate_questions(
            topic=req.topic,
            language=req.language,
            duration_minutes=req.duration_minutes,
            easy_count=req.easy_count,
            medium_count=req.medium_count,
            hard_count=req.hard_count,
            description=req.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"Gemini question generation failed: {str(e)}")
    except Exception as e:
        logger.exception("[DemoRouter] Unexpected error in generate_assessment_questions")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    return {"questions": questions, "total": len(questions)}


@router.post("/assessments/confirm")
async def confirm_assessment(
    req: ConfirmAssessmentRequest,
    user: dict = Depends(require_authority),
):
    """Persist the confirmed (possibly edited) assessment to DemoStore."""
    assessment = DemoStore.create_assessment({
        "title": req.title,
        "description": req.description,
        "duration_minutes": req.duration_minutes,
        "language": req.language,
        "topic": req.topic,
        "difficulty_distribution": {
            "EASY": req.easy_count,
            "MEDIUM": req.medium_count,
            "HARD": req.hard_count,
        },
        "total_questions": len(req.questions),
        "questions": req.questions,
    })
    return assessment


@router.get("/assessments")
async def list_assessments(user: dict = Depends(require_authority)):
    return DemoStore.get_assessments()


@router.get("/assessments/{assessment_id}")
async def get_assessment(assessment_id: str, user: dict = Depends(get_demo_user)):
    ass = DemoStore.get_assessment(assessment_id)
    if not ass:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return ass


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------

@router.get("/candidates")
async def list_candidates(user: dict = Depends(require_authority)):
    """Return demo candidates with their current assignment status."""
    candidates = []
    for c in DEMO_CANDIDATES:
        assignment = DemoStore.get_intern_assignment(c["email"])
        candidate_data = dict(c)
        if assignment:
            ass = DemoStore.get_assessment(assignment["assessment_id"])
            candidate_data["status"] = assignment["status"]
            candidate_data["assigned_assessment"] = ass["title"] if ass else None
            candidate_data["assignment_id"] = assignment["id"]
        candidates.append(candidate_data)
    return candidates


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

@router.post("/assignments/assign")
async def assign_assessment(
    req: AssignRequest,
    user: dict = Depends(require_authority),
):
    """Assign an assessment to an intern by email."""
    # Validate assessment exists
    ass = DemoStore.get_assessment(req.assessment_id)
    if not ass:
        raise HTTPException(status_code=404, detail=f"Assessment '{req.assessment_id}' not found.")

    # Validate intern email is a known demo user
    if req.intern_email not in DEMO_USERS:
        raise HTTPException(
            status_code=404,
            detail=f"No demo user found with email '{req.intern_email}'. Use intern@test.com.",
        )

    if DEMO_USERS[req.intern_email]["role"] != "intern":
        raise HTTPException(status_code=400, detail="The specified user is not an intern.")

    # Check if already assigned
    existing = DemoStore.get_intern_assignment(req.intern_email)
    if existing:
        # Re-assign (overwrite for demo flexibility)
        pass

    assignment = DemoStore.assign_assessment(req.assessment_id, req.intern_email)
    return {
        "message": f"Assessment successfully assigned to {req.intern_email}",
        "assignment": assignment,
        "assessment": ass,
    }


@router.get("/assignments/me")
async def get_my_assignment(user: dict = Depends(require_intern)):
    """Intern gets their assigned assessment."""
    intern_email = user["email"]
    assignment = DemoStore.get_intern_assignment(intern_email)
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="No assessment is currently assigned to you. Please wait for the admin to assign one.",
        )

    ass = DemoStore.get_assessment(assignment["assessment_id"])
    if not ass:
        raise HTTPException(status_code=404, detail="Assigned assessment not found.")

    return {
        "assignment": assignment,
        "assessment": ass,
    }


@router.post("/assignments/start")
async def start_assignment(user: dict = Depends(require_intern)):
    """Mark the intern's assignment as started."""
    assignment = DemoStore.start_assignment(user["email"])
    if not assignment:
        raise HTTPException(status_code=404, detail="No assignment found.")
    return assignment


# ---------------------------------------------------------------------------
# Code Execution (Real Judge0)
# ---------------------------------------------------------------------------

@router.post("/execute/run")
async def run_code(req: RunCodeRequest, user: dict = Depends(get_demo_user)):
    """Run code through Judge0. Returns execution result."""
    if not req.source_code.strip():
        raise HTTPException(status_code=400, detail="Source code cannot be empty.")
    if not req.language.strip():
        raise HTTPException(status_code=400, detail="Language must be specified.")

    try:
        result = await judge0_service.execute_code(
            source_code=req.source_code,
            language=req.language,
            stdin=req.stdin,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"Code execution failed: {str(e)}")
    except Exception as e:
        logger.exception("[DemoRouter] Unexpected error in run_code")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    return result


@router.post("/execute/test-cases")
async def run_test_cases(req: RunTestCasesRequest, user: dict = Depends(get_demo_user)):
    """Run code against provided test cases through Judge0."""
    if not req.source_code.strip():
        raise HTTPException(status_code=400, detail="Source code cannot be empty.")
    if not req.test_cases:
        raise HTTPException(status_code=400, detail="No test cases provided.")
    if len(req.test_cases) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 test cases per request.")

    try:
        results = await judge0_service.run_test_cases(
            source_code=req.source_code,
            language=req.language,
            test_cases=req.test_cases,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"Test case execution failed: {str(e)}")
    except Exception as e:
        logger.exception("[DemoRouter] Unexpected error in run_test_cases")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    passed = sum(1 for r in results if r.get("passed"))
    return {
        "results": results,
        "passed": passed,
        "total": len(results),
        "all_passed": passed == len(results),
    }


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------

def _trigger_gemini_review_background(submission_id: str, assessment: dict, submission: dict):
    """Run Gemini review asynchronously after submission.
    
    This is called as a FastAPI BackgroundTask (sync wrapper). It schedules
    the async work using asyncio.run() in a dedicated event loop so it works
    correctly outside the request's event loop context.
    """
    import asyncio

    async def _run():
        questions = assessment.get("questions", [])
        code_by_question = submission.get("code_by_question", {})
        language = submission.get("final_language", "python")

        all_judge_results = []
        best_code = ""
        best_question = {}

        # Find the first question that has submitted code
        for q in questions:
            q_id = q.get("id", "")
            code_data = code_by_question.get(q_id, {})
            code = code_data.get("code", "")
            if code and not best_code:
                best_code = code
                best_question = q

        if not best_code:
            # Collect any code available
            for q_id, code_data in code_by_question.items():
                best_code = code_data.get("code", "")
                if best_code:
                    break

        if not best_code:
            DemoStore.save_gemini_review(submission_id, {
                "overall_score": 0,
                "summary": "No code submitted.",
                "strengths": [],
                "weaknesses": ["No code was submitted for review."],
                "suggestions": ["Submit working code for a proper review."],
                "error": "No code found in submission.",
            })
            return

        try:
            review = await gemini_service.review_code(
                question=best_question,
                submitted_code=best_code,
                language=language,
                judge_results=all_judge_results,
            )
            review["reviewed_question_title"] = best_question.get("title", "Code Review")
            DemoStore.save_gemini_review(submission_id, review)
            logger.info("[DemoRouter] Gemini review saved for submission %s", submission_id)
        except Exception as e:
            logger.error("[DemoRouter] Gemini review failed for %s: %s", submission_id, str(e))
            DemoStore.save_gemini_review(submission_id, {
                "overall_score": None,
                "summary": "AI review unavailable.",
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
                "error": str(e),
            })

    # Run in a new event loop (background thread has no running loop)
    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error("[DemoRouter] Background review task failed entirely: %s", str(e))


@router.post("/submissions/submit")
async def submit_assessment(
    req: SubmitAssessmentRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_intern),
):
    """Save intern submission and trigger Gemini review in background."""
    intern_email = user["email"]

    # Validate assignment exists
    assignment = DemoStore.get_intern_assignment(intern_email)
    if not assignment:
        raise HTTPException(status_code=404, detail="No active assignment found.")

    # Validate assessment matches
    if assignment["assessment_id"] != req.assessment_id:
        raise HTTPException(status_code=400, detail="Assessment ID does not match your assignment.")

    ass = DemoStore.get_assessment(req.assessment_id)
    if not ass:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    submission = DemoStore.save_submission({
        "assignment_id": assignment["id"],
        "assessment_id": req.assessment_id,
        "intern_email": intern_email,
        "code_by_question": req.code_by_question,
        "final_language": req.final_language,
    })

    # Trigger Gemini review as background task
    background_tasks.add_task(
        _trigger_gemini_review_background,
        submission["id"],
        ass,
        submission,
    )

    return {
        "message": "Assessment submitted successfully. AI review is being generated.",
        "submission_id": submission["id"],
        "submitted_at": submission["submitted_at"],
    }


@router.get("/submissions")
async def list_submissions(user: dict = Depends(require_authority)):
    """Return all completed submissions (admin view)."""
    submissions = DemoStore.get_submissions()
    result = []
    for sub in submissions:
        ass = DemoStore.get_assessment(sub.get("assessment_id", ""))
        review = DemoStore.get_gemini_review(sub["id"])
        result.append({
            "id": sub["id"],
            "intern_email": sub["intern_email"],
            "intern_name": sub["intern_email"].split("@")[0].capitalize(),
            "assessment_id": sub.get("assessment_id"),
            "assessment_title": ass["title"] if ass else "Unknown Assessment",
            "submitted_at": sub["submitted_at"],
            "status": sub["status"],
            "gemini_review_status": sub.get("gemini_review_status", "PENDING"),
            "overall_score": review.get("overall_score") if review else None,
            "language": sub.get("final_language", "python"),
        })
    return result


@router.get("/submissions/{submission_id}")
async def get_submission_detail(submission_id: str, user: dict = Depends(require_authority)):
    """Return full submission detail for admin review page."""
    sub = DemoStore.get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    ass = DemoStore.get_assessment(sub.get("assessment_id", ""))
    review = DemoStore.get_gemini_review(submission_id)
    assignment = DemoStore.get_intern_assignment(sub.get("intern_email", ""))
    decision = DemoStore.get_decision(submission_id)

    return {
        "submission": sub,
        "assessment": ass,
        "gemini_review": review,
        "assignment": assignment,
        "authority_decision": decision,
    }


@router.get("/submissions/{submission_id}/review-status")
async def get_review_status(submission_id: str, user: dict = Depends(get_demo_user)):
    """Poll endpoint for checking if Gemini review is ready."""
    sub = DemoStore.get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    review = DemoStore.get_gemini_review(submission_id)
    return {
        "submission_id": submission_id,
        "review_status": sub.get("gemini_review_status", "PENDING"),
        "review_available": review is not None,
    }


# ---------------------------------------------------------------------------
# Authority Decision
# ---------------------------------------------------------------------------

@router.post("/submissions/{submission_id}/decision")
async def save_authority_decision(
    submission_id: str,
    req: SaveDecisionRequest,
    user: dict = Depends(require_authority),
):
    """Save the authority's hiring decision for a submission."""
    valid_decisions = {"RECOMMENDED", "NEEDS_REVIEW", "NOT_RECOMMENDED"}
    decision_upper = req.decision.upper()
    if decision_upper not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision '{req.decision}'. Must be one of: {', '.join(valid_decisions)}"
        )

    sub = DemoStore.get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    decision = DemoStore.save_decision(submission_id, {
        "submission_id": submission_id,
        "decision": decision_upper,
        "notes": req.notes,
        "decided_by": user["email"],
        "decided_at": datetime.utcnow().isoformat(),
    })
    return {"message": "Decision saved.", "decision": decision}


@router.get("/submissions/{submission_id}/decision")
async def get_authority_decision(
    submission_id: str,
    user: dict = Depends(require_authority),
):
    """Get the authority's hiring decision for a submission."""
    decision = DemoStore.get_decision(submission_id)
    if not decision:
        raise HTTPException(status_code=404, detail="No decision recorded yet.")
    return decision


# ---------------------------------------------------------------------------
# Demo Reset
# ---------------------------------------------------------------------------

@router.post("/reset")
async def reset_demo(user: dict = Depends(require_authority)):
    """Clear all demo data and restore initial state. Admin only."""
    DemoStore.reset()
    return {
        "message": "Demo state has been reset successfully. All assessments, assignments, submissions, and reviews have been cleared.",
        "reset_at": datetime.utcnow().isoformat(),
    }
