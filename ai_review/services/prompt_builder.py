from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ReviewPromptContext(BaseModel):
    """Strongly-typed context used to build prompts for AI providers."""
    source_code: str = Field(..., description="The raw source code submitted by the intern")
    programming_language: str = Field(..., description="Language of the submission e.g. python, javascript, java, cpp")
    assignment_id: Optional[int] = Field(None, description="ID of the assignment the submission belongs to")
    assignment_description: Optional[str] = Field("Evaluate submission code", description="Problem statement or description")
    difficulty: Optional[str] = Field("Medium", description="Difficulty level of the assignment")
    constraints: Optional[str] = Field("None specified", description="Constraints for the task")
    submission_id: int = Field(..., description="The ID of the submission being reviewed")
    intern_id: Optional[int] = Field(None, description="ID of the intern who made the submission")
    language: Optional[str] = Field(None, description="Programming language alias for UI purposes")
    prompt_version: str = Field("v1", description="Prompt template version (v1, v2, v3)")

PROMPT_TEMPLATES: Dict[str, str] = {
    "v1": """You are an expert Senior Software Engineer conducting an interview-quality code review (similar to Hyring / Google code review).
Evaluate the submitted solution thoroughly and objectively.

[PROBLEM CONTEXT]
Language: {programming_language}
Difficulty: {difficulty}
Constraints: {constraints}
Description: {assignment_description}

[SUBMITTED SOURCE CODE]
```{programming_language}
{source_code}
```

[EVALUATION RUBRIC & WEIGHTS]
Evaluate each metric on a 0-100 scale:
1. Correctness (30%): Functional accuracy, edge case execution, handling of unexpected inputs.
2. Algorithm & Logic (15%): Algorithm selection, data structure choice, core logic soundness.
3. Time Complexity (10%): Optimal time complexity, performance bottlenecks.
4. Space Complexity (5%): Optimal memory utilization.
5. Readability (10%): Code layout, formatting, clarity, naming conventions.
6. Maintainability (10%): Modularization, DRY principle, extensibility.
7. Best Practices (5%): Language-specific idiomatic patterns and conventions.
8. Security (5%): Input validation, injection risks, memory safety, vulnerability checks.
9. Optimization (5%): Refactoring opportunities, CPU/RAM efficiency.
10. Edge Case Handling (5%): Boundary conditions, null checks, overflow/underflow handling.

[REQUIRED OUTPUT FORMAT]
You MUST respond ONLY with a raw, valid JSON object (no markdown formatting, no text before or after the JSON):
{{
    "correctness_score": 85.0,
    "algorithm_score": 90.0,
    "time_complexity_score": 80.0,
    "space_complexity_score": 85.0,
    "readability_score": 90.0,
    "maintainability_score": 85.0,
    "best_practices_score": 80.0,
    "security_score": 95.0,
    "optimization_score": 80.0,
    "edge_case_score": 75.0,
    "confidence_score": 90.0,
    "recommendation": "PASS",
    "time_complexity": "O(N log N)",
    "space_complexity": "O(N)",
    "summary": "Solid solution with good algorithmic structure.",
    "strengths": ["Clean function decomposition", "Good use of standard library"],
    "weaknesses": ["Missing null check on input array"],
    "optimization_suggestions": ["Replace loop with vectorized operation"],
    "score_reasoning": {{
        "correctness": "Handled standard cases well but missed empty array input.",
        "time_complexity": "Sorting step dominates runtime."
    }},
    "code_issue_snippets": [
        {{
            "snippet": "if (arr.length == 0)",
            "issue_description": "Does not account for null array reference.",
            "suggested_fix": "if (arr == null || arr.length == 0)"
        }}
    ],
    "optimized_alternatives": [
        {{
            "title": "Use HashMap for O(N) lookup",
            "original_snippet": "for i in list: for j in list:",
            "optimized_code": "seen = set(); for i in list:",
            "explanation": "Reduces nested loop from O(N^2) to O(N)",
            "expected_performance_gain": "10x speedup for N > 1000"
        }}
    ],
    "expected_improvements": {{
        "time_complexity": "Reduced from O(N^2) to O(N log N)",
        "memory_reduction": "15%"
    }},
    "review_trace": {{
        "analyzed_rules": ["null_pointer_check", "nested_loop_detector", "type_safety"]
    }},
    "structured_findings": {{
        "design_patterns": ["Factory Pattern"],
        "coding_standard_compliance": "95%",
        "security_findings": [],
        "code_smells": ["Long method"],
        "duplicate_code": [],
        "input_validation": "Partial",
        "scalability_assessment": "High"
    }}
}}
""",

    "v2": """You are a Principal Software Architect evaluating code for enterprise production standards.
Evaluate the submitted solution using the prompt specification below:

[PROBLEM CONTEXT]
Language: {programming_language}
Difficulty: {difficulty}
Constraints: {constraints}
Description: {assignment_description}

[SUBMITTED CODE]
```{programming_language}
{source_code}
```

Respond STRICTLY with JSON containing metric scores (correctness_score, algorithm_score, time_complexity_score, space_complexity_score, readability_score, maintainability_score, best_practices_score, security_score, optimization_score, edge_case_score), recommendation (PASS/FAIL/REVIEW), summary, strengths, weaknesses, optimization_suggestions, code_issue_snippets, optimized_alternatives, expected_improvements, review_trace, and structured_findings. Return RAW JSON ONLY.
""",

    "v3": """You are an automated AI code evaluation engine. Perform comprehensive rubric evaluation on:
Language: {programming_language}
Code: {source_code}

Return raw JSON containing all 10 rubric metric scores (0-100), recommendation, complexity details, score reasoning, and code issue snippets. No markdown.
"""
}

class PromptBuilder:
    @staticmethod
    def build_prompt(context: ReviewPromptContext) -> str:
        version = context.prompt_version if context.prompt_version in PROMPT_TEMPLATES else "v1"
        template = PROMPT_TEMPLATES[version]
        return template.format(
            programming_language=context.programming_language,
            difficulty=context.difficulty or "Medium",
            constraints=context.constraints or "None",
            assignment_description=context.assignment_description or "Evaluate submission",
            source_code=context.source_code,
        )

def build_context(submission, prompt_version: str = "v1") -> ReviewPromptContext:
    """Construct a ReviewPromptContext from a Submission ORM instance."""
    assignment = getattr(submission, "assignment", None)
    return ReviewPromptContext(
        source_code=getattr(submission, "code", getattr(submission, "source_code", "")),
        programming_language=getattr(submission, "language", getattr(submission, "programming_language", "python")),
        assignment_id=getattr(submission, "assignment_id", None),
        assignment_description=getattr(assignment, "description", "Evaluate submission code"),
        difficulty=getattr(assignment, "difficulty", "Medium"),
        constraints=getattr(assignment, "constraints", "None"),
        submission_id=submission.id,
        intern_id=getattr(submission, "intern_id", None),
        language=getattr(submission, "language", "python"),
        prompt_version=prompt_version,
    )
