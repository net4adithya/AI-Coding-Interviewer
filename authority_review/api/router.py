from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session

from ..schemas.authority_review import (
    AuthorityReviewAggregatedResponse,
    AuthorityReviewDetailsResponse,
    AuthorityReviewDecisionRequest,
    AuthorityNotesRequest,
    AuthorityReviewListResponse,
)
from ..services.authority_review_service import AuthorityReviewService
from ..repositories.authority_review_repository import AuthorityReviewRepository
from ..exceptions.exceptions import (
    AuthorityReviewNotFoundException,
    SubmissionNotFoundException,
    UnauthorizedReviewException,
)

def get_db():
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_authority(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> dict:
    role = (x_user_role or "AUTHORITY").upper()
    if role == "INTERN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Interns are not authorized to access Authority Reviews or internal notes.",
        )
    user_id = int(x_user_id) if x_user_id and x_user_id.isdigit() else 1
    return {"user_id": user_id, "role": role}

def get_authority_review_service(db: Session = Depends(get_db)) -> AuthorityReviewService:
    repo = AuthorityReviewRepository(db)
    return AuthorityReviewService(db, repo)

router = APIRouter()

@router.get(
    "/{submission_id}",
    response_model=AuthorityReviewAggregatedResponse,
    summary="Get complete aggregated review for a submission",
)
def get_authority_review(
    submission_id: int,
    auth_user: dict = Depends(require_authority),
    service: AuthorityReviewService = Depends(get_authority_review_service),
):
    try:
        return service.get_aggregated_review(submission_id, reviewer_id=auth_user["user_id"])
    except SubmissionNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedReviewException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post(
    "/{submission_id}/approve",
    response_model=AuthorityReviewDetailsResponse,
    summary="Approve submission",
)
def approve_submission(
    submission_id: int,
    payload: Optional[AuthorityReviewDecisionRequest] = None,
    auth_user: dict = Depends(require_authority),
    service: AuthorityReviewService = Depends(get_authority_review_service),
):
    notes = payload.internal_notes if payload else None
    return service.approve_submission(submission_id, reviewer_id=auth_user["user_id"], internal_notes=notes)

@router.post(
    "/{submission_id}/reject",
    response_model=AuthorityReviewDetailsResponse,
    summary="Reject submission",
)
def reject_submission(
    submission_id: int,
    payload: Optional[AuthorityReviewDecisionRequest] = None,
    auth_user: dict = Depends(require_authority),
    service: AuthorityReviewService = Depends(get_authority_review_service),
):
    notes = payload.internal_notes if payload else None
    return service.reject_submission(submission_id, reviewer_id=auth_user["user_id"], internal_notes=notes)

@router.post(
    "/{submission_id}/resubmit",
    response_model=AuthorityReviewDetailsResponse,
    summary="Request submission resubmission",
)
def request_resubmission(
    submission_id: int,
    payload: Optional[AuthorityReviewDecisionRequest] = None,
    auth_user: dict = Depends(require_authority),
    service: AuthorityReviewService = Depends(get_authority_review_service),
):
    notes = payload.internal_notes if payload else None
    return service.request_resubmission(submission_id, reviewer_id=auth_user["user_id"], internal_notes=notes)

@router.post(
    "/{submission_id}/notes",
    response_model=AuthorityReviewDetailsResponse,
    summary="Save internal authority notes",
)
def save_internal_notes(
    submission_id: int,
    payload: AuthorityNotesRequest,
    auth_user: dict = Depends(require_authority),
    service: AuthorityReviewService = Depends(get_authority_review_service),
):
    return service.add_internal_notes(submission_id, reviewer_id=auth_user["user_id"], internal_notes=payload.internal_notes)

@router.get(
    "/",
    response_model=AuthorityReviewListResponse,
    summary="List authority reviews with pagination and filtering",
)
def list_authority_reviews(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    review_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    assignment_id: Optional[int] = Query(None, description="Filter by assignment ID"),
    intern_id: Optional[int] = Query(None, description="Filter by intern ID"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    order: str = Query("desc", description="Sort direction: asc or desc"),
    auth_user: dict = Depends(require_authority),
    service: AuthorityReviewService = Depends(get_authority_review_service),
):
    total, items = service.list_reviews(
        page=page,
        size=size,
        status=review_status,
        assignment_id=assignment_id,
        intern_id=intern_id,
        sort_by=sort_by,
        order=order,
    )
    items_response = [AuthorityReviewDetailsResponse.model_validate(item) for item in items]
    return AuthorityReviewListResponse(
        total=total,
        page=page,
        size=size,
        items=items_response,
    )
