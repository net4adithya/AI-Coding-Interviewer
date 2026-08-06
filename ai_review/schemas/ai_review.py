from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class MetricScoreBreakdown(BaseModel):
    score: float
    weight: float
    reasoning: str

class CodeSnippetIssue(BaseModel):
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    snippet: str
    issue_description: str
    suggested_fix: str

class OptimizedAlternative(BaseModel):
    title: str
    original_snippet: str
    optimized_code: str
    explanation: str
    expected_performance_gain: str

class AIReviewBase(BaseModel):
    submission_id: int
    assignment_id: Optional[int] = None
    intern_id: Optional[int] = None
    language: Optional[str] = None
    provider: Optional[str] = None
    provider_version: Optional[str] = None
    model_name: Optional[str] = None
    review_duration_ms: Optional[int] = None
    prompt_version: Optional[str] = None
    is_deleted: Optional[bool] = False
    deleted_at: Optional[datetime] = None

class AIReviewCreate(AIReviewBase):
    pass

class AIReviewResponse(AIReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    review_status: str
    
    # Weighted Metric Scores (Stored independently in DB)
    overall_score: Optional[float] = None
    correctness_score: Optional[float] = None
    algorithm_score: Optional[float] = None
    time_complexity_score: Optional[float] = None
    space_complexity_score: Optional[float] = None
    readability_score: Optional[float] = None
    maintainability_score: Optional[float] = None
    best_practices_score: Optional[float] = None
    security_score: Optional[float] = None
    performance_score: Optional[float] = None
    edge_case_score: Optional[float] = None
    confidence_score: Optional[float] = None

    recommendation: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    
    ai_summary: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

    score_reasoning: Optional[Dict[str, Any]] = None
    code_issue_snippets: Optional[List[Dict[str, Any]]] = None
    optimized_alternatives: Optional[List[Dict[str, Any]]] = None
    expected_improvements: Optional[Dict[str, Any]] = None
    review_trace: Optional[Dict[str, Any]] = None
    structured_findings: Optional[Dict[str, Any]] = None

    temperature: Optional[float] = None
    token_usage: Optional[Dict[str, Any]] = None

    created_at: datetime
    updated_at: datetime

class AIReviewListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[AIReviewResponse]
