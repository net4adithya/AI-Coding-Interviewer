# python_backend/app/execution/dependencies.py
"""FastAPI dependency providers for the execution module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.editor.dependencies import get_db, get_current_user_context
from app.execution.providers.base import BaseExecutionProvider
from app.execution.providers.factory import get_execution_provider
from app.execution.repositories.execution_repository import ExecutionRepository
from app.execution.services.execution_service import ExecutionService


def get_execution_repository(db: Session = Depends(get_db)) -> ExecutionRepository:
    return ExecutionRepository(db)


def get_execution_service(
    db: Session = Depends(get_db),
    repo: ExecutionRepository = Depends(get_execution_repository),
    provider: BaseExecutionProvider = Depends(get_execution_provider),
) -> ExecutionService:
    return ExecutionService(db=db, execution_repo=repo, provider=provider)
