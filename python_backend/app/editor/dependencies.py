# python_backend/app/editor/dependencies.py
"""FastAPI dependency providers for the editor module.

All database sessions, repositories, and the EditorService are instantiated
here and injected via FastAPI's Depends() mechanism.  Nothing is instantiated
globally inside service classes.
"""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.editor.repositories.draft_repository import DraftRepository
from app.editor.repositories.draft_version_repository import DraftVersionRepository
from app.editor.repositories.template_repository import FileSystemTemplateRepository
from app.editor.services.editor_service import EditorService
from app.editor.tasks import LoggingSubmissionProcessor, SubmissionProcessingInterface

# ── Database session ───────────────────────────────────────────────────────────

def get_db():
    """Yield a SQLAlchemy session and ensure it is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Simple JWT bearer extraction ───────────────────────────────────────────────
from app.api.dependencies import get_current_user_context


# ── Repository providers ───────────────────────────────────────────────────────

def get_draft_repository(db: Session = Depends(get_db)) -> DraftRepository:
    return DraftRepository(db)


def get_draft_version_repository(db: Session = Depends(get_db)) -> DraftVersionRepository:
    return DraftVersionRepository(db)


def get_template_repository() -> FileSystemTemplateRepository:
    return FileSystemTemplateRepository()


from app.execution.tasks import Judge0SubmissionProcessor


def get_submission_processor() -> SubmissionProcessingInterface:
    return Judge0SubmissionProcessor()


# ── Service provider ───────────────────────────────────────────────────────────

def get_editor_service(
    db: Session = Depends(get_db),
    draft_repo: DraftRepository = Depends(get_draft_repository),
    version_repo: DraftVersionRepository = Depends(get_draft_version_repository),
    template_repo: FileSystemTemplateRepository = Depends(get_template_repository),
    processor: SubmissionProcessingInterface = Depends(get_submission_processor),
) -> EditorService:
    return EditorService(
        db=db,
        draft_repo=draft_repo,
        version_repo=version_repo,
        template_repo=template_repo,
        submission_processor=processor,
    )
