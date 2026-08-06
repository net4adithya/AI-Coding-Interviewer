import pytest
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
python_backend_dir = os.path.join(root_dir, "python_backend")
sys.path.insert(0, root_dir)
sys.path.insert(0, python_backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base_class import Base
from static_analysis.models.static_analysis import StaticAnalysis
from static_analysis.repositories.static_analysis_repository import StaticAnalysisRepository
from static_analysis.services.static_analysis_service import StaticAnalysisService
from static_analysis.schemas.static_analysis import StaticAnalysisCreate
from static_analysis.exceptions import DuplicateAnalysisException, UnsupportedLanguageException

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_service_analyze_code_success(db_session):
    repo = StaticAnalysisRepository(db_session)
    service = StaticAnalysisService(repo)

    dto = StaticAnalysisCreate(
        submission_id=101,
        assignment_id=1,
        intern_id=5,
        language="python",
        source_code="def add(a, b):\n    return a + b\n",
    )

    result = service.analyze_code(dto)
    assert result.id is not None
    assert result.submission_id == 101
    assert result.language == "python"
    assert result.analysis_status == "COMPLETED"
    assert result.request_id is not None
    assert result.lines_of_code == 2
    assert result.function_count == 1

def test_service_duplicate_analysis_exception(db_session):
    repo = StaticAnalysisRepository(db_session)
    service = StaticAnalysisService(repo)

    dto = StaticAnalysisCreate(
        submission_id=102,
        language="python",
        source_code="print('hello')",
    )

    service.analyze_code(dto)

    with pytest.raises(DuplicateAnalysisException):
        service.analyze_code(dto)

def test_service_unsupported_language_exception(db_session):
    repo = StaticAnalysisRepository(db_session)
    service = StaticAnalysisService(repo)

    dto = StaticAnalysisCreate(
        submission_id=103,
        language="brainfuck",
        source_code="+++++",
    )

    with pytest.raises(UnsupportedLanguageException):
        service.analyze_code(dto)

def test_service_list_and_soft_delete(db_session):
    repo = StaticAnalysisRepository(db_session)
    service = StaticAnalysisService(repo)

    dto1 = StaticAnalysisCreate(submission_id=201, language="python", source_code="x=1")
    dto2 = StaticAnalysisCreate(submission_id=202, language="java", source_code="class Main {}")

    res1 = service.analyze_code(dto1)
    res2 = service.analyze_code(dto2)

    total, items = service.list_analyses(page=1, size=10)
    assert total == 2
    assert len(items) == 2

    # Soft delete res1
    deleted = service.soft_delete_analysis(res1.id)
    assert deleted is True

    # Confirm soft deleted record is excluded from list and get
    total_after, items_after = service.list_analyses(page=1, size=10)
    assert total_after == 1
    assert service.get_analysis_by_id(res1.id) is None
