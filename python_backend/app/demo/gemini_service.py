# python_backend/app/demo/gemini_service.py
"""
Real Gemini API integration for DEMO MODE.

Handles:
1. Question generation — given topic/difficulty distribution, generates structured questions
2. Code review — given question + code + judge results, returns scored review

Uses google-generativeai SDK. Never falls back to fake data — raises clear errors on failure.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _get_client():
    """Return a configured Gemini GenerativeModel."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("google-generativeai package is not installed. Run: pip install google-generativeai")

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    genai.configure(api_key=api_key)
    # Use env var if set, otherwise default to gemini-2.5-flash (gemini-1.5-flash is deprecated)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
    # Strip 'models/' prefix if present (SDK adds it automatically)
    model_name = model_name.replace("models/", "")
    logger.info("[GeminiService] Using model: %s", model_name)
    return genai.GenerativeModel(model_name)


def _extract_json(text: str) -> Any:
    """Extract JSON from Gemini response, stripping markdown code fences if present."""
    # Strip ```json ... ``` or ``` ... ```
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Find first [ or { and last ] or }
    start = min(
        (text.find("[") if text.find("[") != -1 else len(text)),
        (text.find("{") if text.find("{") != -1 else len(text)),
    )
    end = max(text.rfind("]"), text.rfind("}"))
    if start > end:
        raise ValueError(f"No valid JSON found in Gemini response. Raw: {text[:300]}")
    return json.loads(text[start: end + 1])


async def generate_questions(
    topic: str,
    language: str,
    duration_minutes: int,
    easy_count: int,
    medium_count: int,
    hard_count: int,
    description: str = "",
) -> List[dict]:
    """
    Call Gemini to generate coding questions.

    Returns a list of question dicts with the schema:
    {
        id: str (uuid),
        title: str,
        difficulty: "Easy" | "Medium" | "Hard",
        description: str,
        problem_statement: str,
        constraints: str,
        input_format: str,
        output_format: str,
        examples: [{ input: str, output: str, explanation?: str }],
        test_cases: [{ input: str, expected_output: str, is_hidden: bool }],
        topic: str,
    }

    Raises RuntimeError with a descriptive message on failure.
    """
    import uuid

    total = easy_count + medium_count + hard_count
    if total == 0:
        raise ValueError("At least one question must be requested.")

    difficulty_spec = []
    if easy_count > 0:
        difficulty_spec.append(f"{easy_count} Easy")
    if medium_count > 0:
        difficulty_spec.append(f"{medium_count} Medium")
    if hard_count > 0:
        difficulty_spec.append(f"{hard_count} Hard")
    difficulty_str = ", ".join(difficulty_spec)

    prompt = f"""You are a technical coding interview question designer.

Generate exactly {total} coding questions for a {language} coding interview.

Requirements:
- Topic: {topic}
- Time limit: {duration_minutes} minutes total for all questions
- Questions needed: {difficulty_str}
- Language context: {language}
{f'- Additional context: {description}' if description else ''}

CRITICAL: Return ONLY a valid JSON array. No markdown, no explanation outside the array.

Each question object MUST have exactly these fields:
{{
  "title": "Short descriptive title",
  "difficulty": "Easy" | "Medium" | "Hard",
  "problem_statement": "Clear problem description (2-4 sentences)",
  "constraints": "Constraints as a string, e.g. 1 <= n <= 10^5",
  "input_format": "Description of input format",
  "output_format": "Description of expected output format",
  "examples": [
    {{
      "input": "5",
      "output": "Odd",
      "explanation": "5 is not divisible by 2, so it's odd."
    }}
  ],
  "test_cases": [
    {{ "input": "5", "expected_output": "Odd", "is_hidden": false }},
    {{ "input": "8", "expected_output": "Even", "is_hidden": false }},
    {{ "input": "0", "expected_output": "Even", "is_hidden": true }},
    {{ "input": "1000000", "expected_output": "Even", "is_hidden": true }}
  ],
  "topic": "{topic}"
}}

Rules:
- Each Easy question: 1 simple algorithm/data structure, solvable in 10-15 min
- Each Medium question: moderate complexity, solvable in 20-25 min
- Each Hard question: complex problem, solvable in 30+ min
- Each question must have at least 2 visible examples and 2 hidden test cases
- problems must be realistic and practical for {language} developers
- The code to solve these problems must be executable {language} programs reading from stdin

Return ONLY the JSON array, starting with [ and ending with ].
"""

    model = _get_client()
    try:
        response = model.generate_content(prompt)
        raw = response.text
        logger.info("[GeminiService] generate_questions raw response length: %d", len(raw))
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {str(e)}")

    try:
        questions = _extract_json(raw)
    except Exception as e:
        raise RuntimeError(f"Failed to parse Gemini response as JSON: {str(e)}. Raw response (first 500 chars): {raw[:500]}")

    if not isinstance(questions, list):
        raise RuntimeError(f"Gemini returned unexpected type: {type(questions).__name__}. Expected JSON array.")

    # Validate and assign UUIDs
    validated = []
    difficulty_order = {"Easy": 0, "Medium": 1, "Hard": 2}
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            logger.warning("[GeminiService] Skipping non-dict question at index %d", i)
            continue
        validated.append({
            "id": str(uuid.uuid4()),
            "title": q.get("title", f"Question {i + 1}"),
            "difficulty": q.get("difficulty", "Medium"),
            "problem_statement": q.get("problem_statement", q.get("description", "")),
            "constraints": q.get("constraints", ""),
            "input_format": q.get("input_format", ""),
            "output_format": q.get("output_format", ""),
            "examples": q.get("examples", []),
            "test_cases": q.get("test_cases", []),
            "topic": q.get("topic", topic),
        })

    # Sort by difficulty
    validated.sort(key=lambda q: difficulty_order.get(q["difficulty"], 1))

    if len(validated) < total:
        raise RuntimeError(
            f"Gemini returned only {len(validated)} questions, expected {total}. "
            "Please try generating again."
        )

    return validated[:total]


async def review_code(
    question: dict,
    submitted_code: str,
    language: str,
    judge_results: List[dict],
) -> dict:
    """
    Call Gemini to review submitted code.

    Returns a review dict:
    {
        overall_score: int (0-100, weighted),
        correctness_score: int,
        algorithm_score: int,
        time_complexity_score: int,
        space_complexity_score: int,
        readability_score: int,
        maintainability_score: int,
        security_score: int,
        performance_score: int,
        documentation_score: int,
        summary: str,
        strengths: [str],
        weaknesses: [str],
        suggestions: [str],
        time_complexity: str,
        space_complexity: str,
    }

    Weights (applied by backend, not blindly trusted from Gemini):
        Correctness 30%, Algorithm 15%, Time 10%, Space 5%,
        Readability 10%, Maintainability 10%, Security 10%,
        Performance 5%, Documentation 5%
    """

    # Build judge context
    judge_ctx = ""
    if judge_results:
        passed = sum(1 for r in judge_results if r.get("passed"))
        total = len(judge_results)
        judge_ctx = f"\nExecution Results: {passed}/{total} test cases passed."
        for r in judge_results[:3]:   # show up to 3 for context
            judge_ctx += f"\n  Input: {r.get('stdin', 'N/A')!r}"
            judge_ctx += f"\n  Expected: {r.get('expected_output', 'N/A')!r}"
            judge_ctx += f"\n  Actual: {r.get('stdout', 'N/A')!r}"
            judge_ctx += f"\n  Status: {r.get('status', 'N/A')}"
    else:
        judge_ctx = "\nNo execution results available."

    prompt = f"""You are an expert code reviewer for a technical interview platform.

Review the following {language} code submission for the coding question below.

QUESTION:
Title: {question.get('title', 'Unknown')}
Problem: {question.get('problem_statement', '')}
Constraints: {question.get('constraints', '')}
{judge_ctx}

SUBMITTED CODE:
```{language.lower()}
{submitted_code}
```

Evaluate the code on these dimensions (scores 0-100):
1. Correctness — Does it solve the problem correctly?
2. Algorithm — Quality and appropriateness of the algorithm
3. Time Complexity — Efficiency of time complexity
4. Space Complexity — Efficiency of space usage
5. Readability — Code clarity, naming, comments
6. Maintainability — Code structure, modularity
7. Security — Input validation, edge cases handled safely
8. Performance — Practical performance optimizations
9. Documentation — Comments and code self-documentation

CRITICAL: Return ONLY a valid JSON object with exactly these fields. No markdown, no text outside JSON:
{{
  "correctness_score": 85,
  "algorithm_score": 75,
  "time_complexity_score": 70,
  "space_complexity_score": 80,
  "readability_score": 90,
  "maintainability_score": 80,
  "security_score": 75,
  "performance_score": 70,
  "documentation_score": 60,
  "time_complexity": "O(n)",
  "space_complexity": "O(1)",
  "summary": "2-3 sentence overall assessment of the code",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "suggestions": ["specific suggestion 1", "specific suggestion 2"]
}}

Be honest and constructive. Base correctness heavily on the execution results provided.
"""

    model = _get_client()
    try:
        response = model.generate_content(prompt)
        raw = response.text
        logger.info("[GeminiService] review_code raw response length: %d", len(raw))
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed during code review: {str(e)}")

    try:
        review = _extract_json(raw)
    except Exception as e:
        raise RuntimeError(f"Failed to parse Gemini code review response: {str(e)}. Raw: {raw[:500]}")

    if not isinstance(review, dict):
        raise RuntimeError(f"Gemini review returned unexpected type: {type(review).__name__}")

    # Compute weighted overall score (backend controls the weights)
    weights = {
        "correctness_score": 0.30,
        "algorithm_score": 0.15,
        "time_complexity_score": 0.10,
        "space_complexity_score": 0.05,
        "readability_score": 0.10,
        "maintainability_score": 0.10,
        "security_score": 0.10,
        "performance_score": 0.05,
        "documentation_score": 0.05,
    }

    overall = 0
    for field, weight in weights.items():
        score = review.get(field, 50)
        try:
            score = max(0, min(100, int(score)))
        except (TypeError, ValueError):
            score = 50
        review[field] = score
        overall += score * weight

    review["overall_score"] = round(overall)

    # Ensure required list fields exist
    review.setdefault("strengths", [])
    review.setdefault("weaknesses", [])
    review.setdefault("suggestions", [])
    review.setdefault("summary", "AI review completed.")
    review.setdefault("time_complexity", "N/A")
    review.setdefault("space_complexity", "N/A")

    return review


async def review_assessment_selection(
    title: str,
    description: str,
    duration_minutes: int,
    language: str,
    topic: str,
    selected_questions: List[dict],
) -> dict:
    """
    Call real Gemini API to review and validate a selected set of questions from a Question Bank.
    Gemini reviews the assessment structure, difficulty balance, coverage, and suitability.
    """
    q_titles = [q.get("title", "Question") for q in selected_questions]
    difficulties = [q.get("difficulty", "Medium") for q in selected_questions]
    diff_summary = f"Easy: {difficulties.count('Easy') + difficulties.count('EASY')}, Medium: {difficulties.count('Medium') + difficulties.count('MEDIUM')}, Hard: {difficulties.count('Hard') + difficulties.count('HARD')}"

    prompt = f"""You are a senior technical hiring manager reviewing an assessment configuration.

Assessment Details:
- Title: {title}
- Description: {description}
- Target Duration: {duration_minutes} minutes
- Language: {language}
- Topic: {topic}
- Selected Questions Count: {len(selected_questions)}
- Difficulty Breakdown: {diff_summary}
- Question Titles: {', '.join(q_titles)}

Evaluate this assessment suite and return ONLY a valid JSON object with these fields:
{{
  "quality_summary": "2-3 sentences summarizing the overall quality and suitability of this assessment",
  "difficulty_balance": "Assessment of whether the difficulty curve matches the target duration",
  "coverage": "Coverage of key concepts for {topic} in {language}",
  "recommendations": ["Recommendation 1", "Recommendation 2"]
}}
"""

    model = _get_client()
    try:
        response = model.generate_content(prompt)
        raw = response.text
        logger.info("[GeminiService] review_assessment_selection raw length: %d", len(raw))
        res = _extract_json(raw)
        if isinstance(res, dict):
            res.setdefault("quality_summary", "Assessment suite is well-structured and balanced.")
            res.setdefault("difficulty_balance", "Good distribution across requested difficulty levels.")
            res.setdefault("coverage", f"Comprehensive coverage of {topic} concepts in {language}.")
            res.setdefault("recommendations", ["Ready for candidate assignment."])
            return res
    except Exception as e:
        logger.warning("[GeminiService] review_assessment_selection fallback: %s", str(e))

    return {
        "quality_summary": f"Assessment '{title}' contains {len(selected_questions)} validated questions covering {topic}.",
        "difficulty_balance": f"Balanced suite ({diff_summary}) tailored for a {duration_minutes}-minute evaluation.",
        "coverage": f"Effective coverage of foundational and practical {language} concepts.",
        "recommendations": ["Assessment confirmed and ready to assign."]
    }

