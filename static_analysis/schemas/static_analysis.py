from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class StaticAnalysisBase(BaseModel):
    submission_id: int
    assignment_id: Optional[int] = None
    intern_id: Optional[int] = None
    language: str

class StaticAnalysisCreate(StaticAnalysisBase):
    source_code: str = Field(..., description="Source code string to analyze")

class StaticAnalysisResponse(StaticAnalysisBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str
    analysis_status: str
    lines_of_code: Optional[int] = None
    blank_lines: Optional[int] = None
    comment_lines: Optional[int] = None
    comment_ratio: Optional[float] = None
    cyclomatic_complexity: Optional[int] = None
    cognitive_complexity: Optional[int] = None
    maintainability_index: Optional[float] = None
    duplicate_lines: Optional[int] = None
    duplicate_percentage: Optional[float] = None
    function_count: Optional[int] = None
    class_count: Optional[int] = None
    variable_count: Optional[int] = None
    maximum_nesting_depth: Optional[int] = None
    security_warning_count: Optional[int] = None
    style_violation_count: Optional[int] = None
    code_smell_count: Optional[int] = None
    analysis_duration_ms: Optional[int] = None
    analyzer_name: Optional[str] = None
    analyzer_version: Optional[str] = None
    structured_output: Optional[dict] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class StaticAnalysisListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[StaticAnalysisResponse]
