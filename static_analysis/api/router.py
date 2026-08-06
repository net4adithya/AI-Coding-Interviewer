from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from ..schemas.static_analysis import (
    StaticAnalysisCreate,
    StaticAnalysisResponse,
    StaticAnalysisListResponse,
)
from ..services.static_analysis_service import StaticAnalysisService
from ..repositories.static_analysis_repository import StaticAnalysisRepository
from ..exceptions import (
    DuplicateAnalysisException,
    UnsupportedLanguageException,
    AnalysisFailedException,
    AnalyzerNotFoundException,
)

# Helper dependency to get DB session if not imported from global app
def get_db():
    from app.db.session import SessionLocal  # Fallback to standard DB session
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_static_analysis_service(db: Session = Depends(get_db)) -> StaticAnalysisService:
    repo = StaticAnalysisRepository(db)
    return StaticAnalysisService(repo)

router = APIRouter()

@router.post(
    "/",
    response_model=StaticAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit source code for static analysis",
)
def create_static_analysis(
    payload: StaticAnalysisCreate,
    service: StaticAnalysisService = Depends(get_static_analysis_service),
):
    try:
        return service.analyze_code(payload)
    except DuplicateAnalysisException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except UnsupportedLanguageException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AnalysisFailedException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except AnalyzerNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/{analysis_id}",
    response_model=StaticAnalysisResponse,
    summary="Get static analysis record by ID",
)
def get_static_analysis(
    analysis_id: int,
    service: StaticAnalysisService = Depends(get_static_analysis_service),
):
    record = service.get_analysis_by_id(analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Static analysis record with ID {analysis_id} not found",
        )
    return record

@router.get(
    "/",
    response_model=StaticAnalysisListResponse,
    summary="List static analysis records with filtering and pagination",
)
def list_static_analyses(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    assignment_id: Optional[int] = Query(None, description="Filter by assignment ID"),
    intern_id: Optional[int] = Query(None, description="Filter by intern ID"),
    language: Optional[str] = Query(None, description="Filter by language"),
    analysis_status: Optional[str] = Query(None, description="Filter by status"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    order: str = Query("desc", description="Sort direction: asc or desc"),
    service: StaticAnalysisService = Depends(get_static_analysis_service),
):
    total, items = service.list_analyses(
        page=page,
        size=size,
        assignment_id=assignment_id,
        intern_id=intern_id,
        language=language,
        analysis_status=analysis_status,
        sort_by=sort_by,
        order=order,
    )
    return StaticAnalysisListResponse(
        total=total,
        page=page,
        size=size,
        items=items,
    )

@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a static analysis record",
)
def delete_static_analysis(
    analysis_id: int,
    service: StaticAnalysisService = Depends(get_static_analysis_service),
):
    deleted = service.soft_delete_analysis(analysis_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Static analysis record with ID {analysis_id} not found",
        )
    return None
