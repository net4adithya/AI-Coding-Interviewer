# python_backend/app/assessment/api/router.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List

from app.assessment.schemas.question_bank import QuestionBankResponse, QuestionBankDetailResponse
from app.assessment.schemas.assessment import (
    AssessmentCreateRequest, AssessmentResponse, AssignAssessmentRequest, AssessmentInternResponse
)
from app.assessment.schemas.question import ParsedQuestionSchema
from app.assessment.services.question_bank_service import QuestionBankService
from app.assessment.services.assessment_service import AssessmentService
from app.assessment.api.dependencies import (
    get_question_bank_service, get_assessment_service, require_authority, require_intern, get_current_user_context
)

router = APIRouter()

# ── Question Bank ─────────────────────────────────────────────────────────────

@router.post("/question-banks/upload", response_model=QuestionBankDetailResponse)
def upload_question_bank(
    file: UploadFile = File(...),
    qb_service: QuestionBankService = Depends(get_question_bank_service),
    user_ctx: dict = Depends(require_authority)
):
    """Upload a PDF file and parse it into a question bank."""
    print(f"=== UPLOAD DIAGNOSTIC ===")
    print(f"filename: {file.filename}")
    print(f"content_type: {file.content_type}")
    print(f"size: {file.size if hasattr(file, 'size') else 'unknown'}")
    
    if not file.filename.lower().endswith(".pdf"):
        print("Error: Not a PDF")
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")
        
    try:
        res = qb_service.upload_and_parse(
            owner_id=user_ctx["user_id"],
            filename=file.filename,
            file_stream=file.file
        )
        print(f"SUCCESS: Extracted {len(res.questions)} questions")
        return res
    except ValueError as e:
        import traceback
        traceback.print_exc()
        print(f"ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/question-banks", response_model=List[QuestionBankResponse])
def get_question_banks(
    qb_service: QuestionBankService = Depends(get_question_bank_service),
    user_ctx: dict = Depends(require_authority)
):
    """Get all uploaded question banks."""
    return qb_service.get_all()

@router.get("/question-banks/{id}", response_model=QuestionBankResponse)
def get_question_bank(
    id: int,
    qb_service: QuestionBankService = Depends(get_question_bank_service),
    user_ctx: dict = Depends(require_authority)
):
    """Get a specific question bank."""
    bank = qb_service.get_by_id(id)
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found.")
    return bank

@router.get("/question-banks/{id}/questions")
def get_question_bank_questions(
    id: int,
    qb_service: QuestionBankService = Depends(get_question_bank_service),
    user_ctx: dict = Depends(require_authority)
):
    """Get questions for a specific question bank."""
    questions = qb_service.get_questions(id)
    return questions


# ── Assessment Configuration ──────────────────────────────────────────────────

@router.post("/", response_model=AssessmentResponse)
def create_assessment(
    req: AssessmentCreateRequest,
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(require_authority)
):
    """Create a new assessment configuration."""
    try:
        return ass_service.create_assessment(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[AssessmentResponse])
def get_assessments(
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(get_current_user_context)
):
    """Get all assessments."""
    return ass_service.repo.get_all()

@router.get("/intern/me", response_model=AssessmentResponse)
def get_my_assessment(
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(require_intern)
):
    """Get the assessment assigned to the current intern."""
    intern_id = user_ctx["user_id"]
    print(f"[get_my_assessment] intern local user_id={intern_id}", flush=True)

    assignments = ass_service.repo.get_assignments_for_intern(intern_id)
    print(f"[get_my_assessment] assignments found: {len(assignments)}", flush=True)
    for a in assignments:
        print(f"  assignment id={a.id} assessment_id={a.assessment_id} status={a.status}", flush=True)

    assignment = assignments[0] if assignments else None
    if not assignment:
        print(f"[get_my_assessment] No assignment for intern_id={intern_id}", flush=True)
        raise HTTPException(status_code=404, detail="No assessment assigned to you.")

    ass = ass_service.repo.get_by_id(assignment.assessment_id)
    if not ass:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    print(f"[get_my_assessment] Returning assessment id={ass.id} title={ass.title!r} status={ass.status}", flush=True)

    # Build response safely using from_orm to avoid SQLAlchemy internal state leaking into Pydantic
    response = AssessmentResponse.from_orm(ass)
    response.assignment_id = assignment.id
    return response

@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: int,
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(get_current_user_context)
):
    """Get assessment config. Interns can only access if assigned."""
    ass = ass_service.repo.get_by_id(assessment_id)
    if not ass:
        raise HTTPException(status_code=404, detail="Assessment not found.")
        
    role = user_ctx.get("role", "").lower()
    if role == "intern":
        assignment = ass_service.repo.get_assignment(assessment_id, user_ctx["user_id"])
        if not assignment:
            raise HTTPException(status_code=403, detail="Assessment not assigned to you.")
    
    return ass

@router.get("/{assessment_id}/questions", response_model=List[ParsedQuestionSchema])
def get_assessment_questions(
    assessment_id: int,
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(get_current_user_context)
):
    """Get questions for the assessment. Interns only if assigned."""
    role = user_ctx.get("role", "").lower()
    if role == "intern":
        assignment = ass_service.repo.get_assignment(assessment_id, user_ctx["user_id"])
        if not assignment:
            raise HTTPException(status_code=403, detail="Assessment not assigned to you.")
            
    questions = ass_service.repo.get_assessment_questions(assessment_id)
    return questions

@router.post("/{assessment_id}/preview")
async def preview_assessment(
    assessment_id: int,
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(require_authority)
):
    """Preview AI or Fallback question selection without saving."""
    try:
        questions = await ass_service.preview_selection(assessment_id)
        return questions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{assessment_id}/generate", response_model=AssessmentResponse)
async def generate_assessment(
    assessment_id: int,
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(require_authority)
):
    """Generate and lock the assessment question set."""
    try:
        return await ass_service.generate_assessment(assessment_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{assessment_id}/publish", response_model=AssessmentResponse)
def publish_assessment(
    assessment_id: int,
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(require_authority)
):
    """Publish the generated assessment."""
    try:
        return ass_service.publish_assessment(assessment_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{assessment_id}/assign", response_model=AssessmentInternResponse)
def assign_assessment(
    assessment_id: int,
    req: AssignAssessmentRequest,
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(require_authority)
):
    """Assign a published assessment to an intern."""
    try:
        return ass_service.assign_assessment(assessment_id, req.intern_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from app.users.models import User
from app.assessment.schemas.assessment import AssignAssessmentEmailRequest

@router.post("/{assessment_id}/assign-email", response_model=AssessmentInternResponse)
def assign_assessment_by_email(
    assessment_id: int,
    req: AssignAssessmentEmailRequest,
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(require_authority)
):
    """Assign a published assessment to an intern by email."""
    from app.users.models import RoleEnum
    import traceback as _tb

    db = ass_service.repo.db
    print(f"[assign-email] assessment_id={assessment_id} email={req.email!r}", flush=True)

    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Intern with this email was not found.")

    print(f"[assign-email] Found user id={user.id} role={user.role}", flush=True)

    if user.role != RoleEnum.INTERN:
        raise HTTPException(status_code=400, detail="This user is not registered as an intern.")

    try:
        result = ass_service.assign_assessment(assessment_id, user.id)
        print(f"[assign-email] Assignment created id={result.id}", flush=True)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        _tb.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from app.assessment.schemas.assessment import AuthorityDecisionRequest, AuthorityDecisionResponse
from app.assessment.models.assessment import AuthorityDecision

@router.post("/intern/{assignment_id}/decision", response_model=AuthorityDecisionResponse)
def submit_decision(
    assignment_id: int,
    req: AuthorityDecisionRequest,
    ass_service: AssessmentService = Depends(get_assessment_service),
    user_ctx: dict = Depends(require_authority)
):
    """Submit authority decision for an assignment."""
    try:
        db = ass_service.repo.db
        
        # Check if decision already exists
        decision = db.query(AuthorityDecision).filter_by(assessment_intern_id=assignment_id).first()
        if decision:
            decision.decision = req.decision
            decision.reviewer_notes = req.reviewer_notes
        else:
            decision = AuthorityDecision(
                assessment_intern_id=assignment_id,
                decision=req.decision,
                reviewer_notes=req.reviewer_notes
            )
            db.add(decision)
            
        db.commit()
        db.refresh(decision)
        return decision
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
