from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class AuthorityReviewDecisionRequest(BaseModel):
    internal_notes: Optional[str] = Field(None, description="Optional administrative notes for this decision")

class AuthorityNotesRequest(BaseModel):
    internal_notes: str = Field(..., description="Internal notes visible only to Authorities")

class SubmissionInfoResponse(BaseModel):
    submission_id: int
    intern_id: Optional[int] = None
    intern_name: Optional[str] = None
    intern_email: Optional[str] = None
    assignment_id: Optional[int] = None
    assignment_title: Optional[str] = None
    language: str
    submission_timestamp: Optional[datetime] = None
    status: str

class AIReviewSectionResponse(BaseModel):
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    optimization_suggestions: Optional[List[str]] = None
    complexity_analysis: Optional[Dict[str, Any]] = None
    security_review: Optional[Dict[str, Any]] = None
    performance_review: Optional[Dict[str, Any]] = None

class StaticAnalysisSectionResponse(BaseModel):
    cyclomatic_complexity: Optional[int] = None
    maintainability_index: Optional[float] = None
    security_warnings: Optional[int] = None
    code_smells: Optional[int] = None
    duplicate_code: Optional[Dict[str, Any]] = None
    unused_variables: Optional[int] = None
    structured_output: Optional[Dict[str, Any]] = None

class DockerExecutionSectionResponse(BaseModel):
    execution_time_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    hidden_test_results: Optional[Dict[str, Any]] = None
    is_placeholder: bool = True

class AuthorityReviewDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str
    submission_id: int
    assignment_id: Optional[int] = None
    intern_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    status: str
    decision: Optional[str] = None
    internal_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_version: Optional[str] = None
    review_source: Optional[str] = None
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AuthorityReviewAggregatedResponse(BaseModel):
    submission: SubmissionInfoResponse
    ai_review: Optional[AIReviewSectionResponse] = None
    static_analysis: Optional[StaticAnalysisSectionResponse] = None
    docker_execution: DockerExecutionSectionResponse
    authority_review: AuthorityReviewDetailsResponse

class AuthorityReviewListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[AuthorityReviewDetailsResponse]
