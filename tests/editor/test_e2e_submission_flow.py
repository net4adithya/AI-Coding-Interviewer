# tests/editor/test_e2e_submission_flow.py
"""End-to-end integration test simulating the full intern→submission→authority flow.

Steps (mirrors the spec's 22-step flow):
 1.  Intern opens assignment (GET /session)
 2.  Receives starter code
 3.  Saves draft (POST /draft)
 4.  Saves draft again
 5.  Saves draft multiple times
 6.  Verify version numbers increase
 7.  Retrieve draft (GET /draft/{id})
 8.  Verify version history (GET /draft/{id}/versions)
 9.  Reset draft (POST /draft/{id}/reset)
10.  Verify reset created a new version
11.  Modify code again
12.  Submit (POST /submit)
13.  Verify submission created
14.  Verify draft locked
15.  Attempt another autosave → verify rejected
16.  Authority retrieves submission (GET /submission/{id})
17.  Verify authority sees submitted code
18.  Verify authority cannot modify it
19.  Verify processing task was triggered
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.editor.models.editor import Draft, DraftVersion  # noqa
from static_analysis.models.static_analysis import Submission, Assignment, User, StaticAnalysis  # noqa
from authority_review.models.authority_review import AuthorityReview  # noqa
from app.editor.repositories.draft_repository import DraftRepository
from app.editor.repositories.draft_version_repository import DraftVersionRepository
from app.editor.repositories.template_repository import FileSystemTemplateRepository
from app.editor.schemas.editor import DraftCreateRequest
from app.editor.services.editor_service import EditorService
from app.editor.tasks import SubmissionProcessingInterface
from app.editor.exceptions import DraftLockedError

TEMPLATES_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "python_backend", "templates")
)

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
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


@pytest.fixture()
def entities(db):
    db.query(DraftVersion).delete()
    db.query(Draft).delete()
    db.query(Submission).delete()
    db.commit()

    if not db.query(Assignment).filter(Assignment.id == 1).first():
        db.add(Assignment(id=1))
    if not db.query(User).filter(User.id == 10).first():
        db.add(User(id=10))
    db.commit()
    return {"assignment_id": 1, "intern_id": 10}


def make_service(db, processor):
    return EditorService(
        db=db,
        draft_repo=DraftRepository(db),
        version_repo=DraftVersionRepository(db),
        template_repo=FileSystemTemplateRepository(templates_root=TEMPLATES_ROOT),
        submission_processor=processor,
    )


def test_full_e2e_flow(db, entities):
    mock_processor = MagicMock(spec=SubmissionProcessingInterface)
    svc = make_service(db, mock_processor)

    assignment_id = entities["assignment_id"]
    intern_id = entities["intern_id"]

    # ── Step 1-2: Open session, receive starter code ──────────────────────────
    session = svc.open_session(
        current_user_id=intern_id,
        current_user_role="intern",
        assignment_id=assignment_id,
    )
    assert session.draft_id is not None
    assert session.template.code  # starter code present
    draft_id = session.draft_id
    assert session.draft_version == 1

    # ── Steps 3-5: Multiple autosaves ─────────────────────────────────────────
    codes = ["edit 1", "edit 2", "edit 3"]
    last_resp = None
    for code in codes:
        last_resp = svc.save_draft(
            current_user_id=intern_id,
            current_user_role="intern",
            payload=DraftCreateRequest(
                assignment_id=assignment_id,
                language="python",
                code=code,
            ),
        )

    # ── Step 6: Verify version numbers increase ───────────────────────────────
    # Started at 1 (session creation) + 3 saves = 4
    assert last_resp.current_version == 4

    # ── Step 7: Retrieve draft ────────────────────────────────────────────────
    draft_detail = svc.get_draft(
        current_user_id=intern_id,
        current_user_role="intern",
        draft_id=draft_id,
    )
    assert draft_detail.code == "edit 3"
    assert draft_detail.current_version == 4

    # ── Step 8: Verify version history ────────────────────────────────────────
    history = svc.list_draft_versions(
        current_user_id=intern_id,
        current_user_role="intern",
        draft_id=draft_id,
    )
    assert history.total == 4

    # ── Steps 9-10: Reset draft ───────────────────────────────────────────────
    reset_resp = svc.reset_draft(
        current_user_id=intern_id,
        current_user_role="intern",
        draft_id=draft_id,
    )
    assert reset_resp.current_version == 5
    # Previous versions still intact
    history2 = svc.list_draft_versions(
        current_user_id=intern_id,
        current_user_role="intern",
        draft_id=draft_id,
    )
    assert history2.total == 5

    # ── Step 11: Modify code again ────────────────────────────────────────────
    svc.save_draft(
        current_user_id=intern_id,
        current_user_role="intern",
        payload=DraftCreateRequest(
            assignment_id=assignment_id,
            language="python",
            code="final solution",
        ),
    )

    # ── Step 12-14: Submit ────────────────────────────────────────────────────
    sub_resp = svc.submit_draft(
        current_user_id=intern_id,
        current_user_role="intern",
        draft_id=draft_id,
    )
    assert sub_resp.submission_id is not None
    assert sub_resp.draft_locked is True
    assert sub_resp.draft_submitted is True

    # ── Step 15: Autosave after lock must be rejected ─────────────────────────
    with pytest.raises(DraftLockedError):
        svc.save_draft(
            current_user_id=intern_id,
            current_user_role="intern",
            payload=DraftCreateRequest(
                assignment_id=assignment_id,
                language="python",
                code="attempt",
            ),
        )

    # ── Steps 16-18: Authority retrieves submission ────────────────────────────
    detail = svc.get_submission(
        current_user_id=999,
        current_user_role="authority",
        submission_id=sub_resp.submission_id,
    )
    assert detail.code == "final solution"
    assert detail.is_locked is True
    assert detail.submission_id == sub_resp.submission_id

    # ── Step 19: Processing task was triggered ─────────────────────────────────
    mock_processor.trigger.assert_called_once_with(sub_resp.submission_id)
