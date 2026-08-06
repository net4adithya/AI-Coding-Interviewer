import time
import uuid
from typing import List, Optional, Dict, Any, Tuple
from ..models.static_analysis import StaticAnalysis, AnalysisStatusEnum
from ..repositories.static_analysis_repository import StaticAnalysisRepository
from ..schemas.static_analysis import StaticAnalysisCreate
from ..factory.analyzer_factory import AnalyzerFactory
from ..exceptions import DuplicateAnalysisException, AnalysisFailedException, UnsupportedLanguageException

class StaticAnalysisService:
    """Business logic service for static analysis operations."""

    def __init__(self, repository: StaticAnalysisRepository):
        self.repository = repository

    def analyze_code(self, dto: StaticAnalysisCreate) -> StaticAnalysis:
        """Synchronously execute static analysis for given submission and source code."""
        # 1. Guard against duplicate analysis for the same submission
        existing = self.repository.get_by_submission_id(dto.submission_id)
        if existing:
            raise DuplicateAnalysisException(submission_id=dto.submission_id)

        # 2. Retrieve appropriate analyzer
        analyzer = AnalyzerFactory.get_analyzer(dto.language)

        # 3. Generate tracking UUID
        request_id = str(uuid.uuid4())

        # 4. Perform analysis and track duration
        start_time = time.time()
        try:
            metrics = analyzer.analyze(dto.source_code)
            duration_ms = int((time.time() - start_time) * 1000)
            status = AnalysisStatusEnum.COMPLETED
        except Exception as err:
            duration_ms = int((time.time() - start_time) * 1000)
            raise AnalysisFailedException(reason=str(err))

        # 5. Build static analysis DB model
        analysis_obj = StaticAnalysis(
            request_id=request_id,
            submission_id=dto.submission_id,
            assignment_id=dto.assignment_id,
            intern_id=dto.intern_id,
            language=dto.language.lower(),
            analysis_status=status,
            lines_of_code=metrics.get("lines_of_code"),
            blank_lines=metrics.get("blank_lines"),
            comment_lines=metrics.get("comment_lines"),
            comment_ratio=metrics.get("comment_ratio"),
            cyclomatic_complexity=metrics.get("cyclomatic_complexity"),
            cognitive_complexity=metrics.get("cognitive_complexity"),
            maintainability_index=metrics.get("maintainability_index"),
            duplicate_lines=metrics.get("duplicate_lines"),
            duplicate_percentage=metrics.get("duplicate_percentage"),
            function_count=metrics.get("function_count"),
            class_count=metrics.get("class_count"),
            variable_count=metrics.get("variable_count"),
            maximum_nesting_depth=metrics.get("maximum_nesting_depth"),
            security_warning_count=metrics.get("security_warning_count"),
            style_violation_count=metrics.get("style_violation_count"),
            code_smell_count=metrics.get("code_smell_count"),
            analysis_duration_ms=duration_ms,
            analyzer_name=metrics.get("analyzer_name"),
            analyzer_version=metrics.get("analyzer_version"),
            structured_output=metrics.get("structured_output", {}),
        )

        return self.repository.create(analysis_obj)

    def get_analysis_by_id(self, analysis_id: int) -> Optional[StaticAnalysis]:
        return self.repository.get_by_id(analysis_id)

    def list_analyses(
        self,
        page: int = 1,
        size: int = 20,
        assignment_id: Optional[int] = None,
        intern_id: Optional[int] = None,
        language: Optional[str] = None,
        analysis_status: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> Tuple[int, List[StaticAnalysis]]:
        # Enforce max page size of 100
        size = min(max(size, 1), 100)
        page = max(page, 1)
        skip = (page - 1) * size

        filters = {}
        if assignment_id is not None:
            filters["assignment_id"] = assignment_id
        if intern_id is not None:
            filters["intern_id"] = intern_id
        if language is not None:
            filters["language"] = language.lower()
        if analysis_status is not None:
            filters["analysis_status"] = analysis_status

        return self.repository.list(
            skip=skip,
            limit=size,
            filters=filters,
            sort_by=sort_by,
            order=order,
        )

    def soft_delete_analysis(self, analysis_id: int) -> bool:
        return self.repository.soft_delete(analysis_id)

    async def run_analysis_async(self, dto: StaticAnalysisCreate) -> StaticAnalysis:
        """Asynchronous execution interface method.
        Can be wired to FastAPI BackgroundTasks, Celery, or Redis Queue without modifying the API layer.
        """
        return self.analyze_code(dto)
