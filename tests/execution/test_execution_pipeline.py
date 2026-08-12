# tests/execution/test_execution_pipeline.py
"""End-to-end integration test for full post-submission pipeline."""

import os
import sys
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.editor.models.editor import Draft, DraftVersion  # noqa
from app.execution.models.test_case import TestCase  # noqa
from app.execution.models.execution_result import ExecutionResult  # noqa
from static_analysis.models.static_analysis import Submission, Assignment, User, StaticAnalysis  # noqa
from authority_review.models.authority_review import AuthorityReview  # noqa

from app.editor.repositories.draft_repository import DraftRepository
from app.editor.repositories.draft_version_repository import DraftVersionRepository
from app.editor.repositories.template_repository import FileSystemTemplateRepository
from app.editor.schemas.editor import DraftCreateRequest
from app.editor.services.editor_service import EditorService
from app.execution.tasks.execution_tasks import Judge0SubmissionProcessor
from app.execution.services.execution_service import ExecutionService
from app.execution.repositories.execution_repository import ExecutionRepository
from app.execution.providers.base import BaseExecutionProvider, ExecutionRawResult

TEMPLATES_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "python_backend", "templates")
)

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def make_mock_provider():
    provider = MagicMock(spec=BaseExecutionProvider)
    provider.provider_name.return_value = "judge0"
    provider.provider_version.return_value = "v1"
    provider.execute = AsyncMock(
        return_value=ExecutionRawResult(
            token="tok-e2e-pipeline",
            status_id=3,
            status_description="Accepted",
            stdout="Hello, World!\n",
            execution_time=0.03,
            memory=12500,
        )
    )
    return provider


def test_full_pipeline_execution(db):
    async def _test():
        # Seed assignment and user
        assignment = Assignment(id=1)
        user = User(id=10)
        db.add(assignment)
        db.add(user)
        db.commit()

        processor = Judge0SubmissionProcessor()
        editor_service = EditorService(
            db=db,
            draft_repo=DraftRepository(db),
            version_repo=DraftVersionRepository(db),
            template_repo=FileSystemTemplateRepository(templates_root=TEMPLATES_ROOT),
            submission_processor=processor,
        )

        draft_resp = editor_service.save_draft(
            current_user_id=user.id,
            current_user_role="intern",
            payload=DraftCreateRequest(
                assignment_id=assignment.id,
                language="python",
                code="def main():\n    print('Hello, World!')\n\nmain()\n",
            ),
        )

        sub_resp = editor_service.submit_draft(
            current_user_id=user.id,
            current_user_role="intern",
            draft_id=draft_resp.id,
        )
        sub_id = sub_resp.submission_id
        assert sub_id is not None

        mock_provider = make_mock_provider()
        exec_service = ExecutionService(
            db=db,
            execution_repo=ExecutionRepository(db),
            provider=mock_provider,
        )

        with patch.object(exec_service, "_trigger_static_analysis") as mock_sa, patch.object(
            exec_service, "_trigger_ai_review"
        ) as mock_ai:
            summary = await exec_service.run_execution_pipeline(sub_id)

        assert summary.submission_id == sub_id
        assert summary.passed_test_cases == 1
        assert summary.pass_percentage == 100.0
        assert summary.max_execution_time == 0.03

        mock_sa.assert_called_once()
        mock_ai.assert_called_once()

    asyncio.run(_test())
