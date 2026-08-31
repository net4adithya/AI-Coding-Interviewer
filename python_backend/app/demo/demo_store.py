# python_backend/app/demo/demo_store.py
"""
Centralised in-memory data store for DEMO MODE.

This module provides a single shared DemoStore class that acts as the
database replacement when DEMO_MODE=true.  All data lives in Python
module-level dictionaries and is lost on server restart (expected for demo).

Usage:
    from app.demo.demo_store import DemoStore

    DemoStore.create_assessment(data)
    DemoStore.get_assessments()
    DemoStore.assign_assessment(assessment_id, intern_email)
    DemoStore.get_intern_assignment(intern_email)
    DemoStore.save_submission(data)
    DemoStore.save_gemini_review(submission_id, review)
    DemoStore.reset()
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Module-level storage (shared across the process lifetime)
# ---------------------------------------------------------------------------
_assessments: Dict[str, dict] = {}          # id -> assessment dict
_assignments: Dict[str, dict] = {}          # id -> assignment dict  (email -> assignment too)
_submissions: Dict[str, dict] = {}          # id -> submission dict
_gemini_reviews: Dict[str, dict] = {}       # submission_id -> review dict
_judge_results: Dict[str, List[dict]] = {}  # run_id -> list of result dicts
_decisions: Dict[str, dict] = {}            # submission_id -> authority decision dict
_question_banks: Dict[str, dict] = {}       # id -> question_bank dict


# Seed initial default Question Bank for demo readiness
def _seed_default_question_bank():
    bank_id = "qb-default-001"
    if bank_id not in _question_banks:
        _question_banks[bank_id] = {
            "id": bank_id,
            "title": "Odd or Even & Algorithms Question Bank",
            "topic": "Algorithms",
            "description": "Standard algorithms question bank uploaded from PDF",
            "created_at": datetime.utcnow().isoformat(),
            "questions": [
                {
                    "id": "qb-q-001",
                    "title": "Odd or Even Number",
                    "difficulty": "Easy",
                    "topic": "Algorithms",
                    "problem_statement": "Given an integer N, determine whether it is odd or even. Print 'Odd' or 'Even'.",
                    "constraints": "1 <= N <= 10^9",
                    "input_format": "A single integer N.",
                    "output_format": "Print 'Odd' if N is odd, otherwise print 'Even'.",
                    "examples": [{"input": "7", "output": "Odd"}, {"input": "4", "output": "Even"}],
                    "test_cases": [
                        {"input": "7", "expected_output": "Odd", "is_hidden": False},
                        {"input": "4", "expected_output": "Even", "is_hidden": False},
                        {"input": "100", "expected_output": "Even", "is_hidden": True},
                    ]
                },
                {
                    "id": "qb-q-002",
                    "title": "Sum of Array Elements",
                    "difficulty": "Easy",
                    "topic": "Algorithms",
                    "problem_statement": "Given a JSON array of numbers, return the sum of all elements.",
                    "constraints": "1 <= len(arr) <= 1000",
                    "input_format": "JSON array string e.g. [1, 2, 3]",
                    "output_format": "Sum integer e.g. 6",
                    "examples": [{"input": "[1, 2, 3, 4]", "output": "10"}],
                    "test_cases": [
                        {"input": "[1, 2, 3, 4]", "expected_output": "10", "is_hidden": False},
                        {"input": "[10, -2, 5]", "expected_output": "13", "is_hidden": True},
                    ]
                },
                {
                    "id": "qb-q-003",
                    "title": "Two Sum Target Pair",
                    "difficulty": "Medium",
                    "topic": "Algorithms",
                    "problem_statement": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
                    "constraints": "2 <= nums.length <= 10^4",
                    "input_format": "Line 1: JSON array nums\nLine 2: Target integer",
                    "output_format": "JSON array of 2 indices e.g. [0, 1]",
                    "examples": [{"input": "[2, 7, 11, 15]\n9", "output": "[0, 1]"}],
                    "test_cases": [
                        {"input": "[2, 7, 11, 15]\n9", "expected_output": "[0, 1]", "is_hidden": False},
                        {"input": "[3, 2, 4]\n6", "expected_output": "[1, 2]", "is_hidden": True},
                    ]
                },
                {
                    "id": "qb-q-004",
                    "title": "Valid Anagram String",
                    "difficulty": "Medium",
                    "topic": "Data Structures",
                    "problem_statement": "Given two strings s and t, return true if t is an anagram of s, and false otherwise.",
                    "constraints": "1 <= s.length, t.length <= 5 * 10^4",
                    "input_format": "Line 1: string s\nLine 2: string t",
                    "output_format": "true or false",
                    "examples": [{"input": "anagram\nagaram", "output": "true"}],
                    "test_cases": [
                        {"input": "anagram\nagaram", "expected_output": "true", "is_hidden": False},
                        {"input": "rat\ncar", "expected_output": "false", "is_hidden": True},
                    ]
                },
                {
                    "id": "qb-q-005",
                    "title": "Longest Palindromic Substring",
                    "difficulty": "Hard",
                    "topic": "Algorithms",
                    "problem_statement": "Given a string s, return the longest palindromic substring in s.",
                    "constraints": "1 <= s.length <= 1000",
                    "input_format": "Single string s",
                    "output_format": "Longest palindromic substring",
                    "examples": [{"input": "babad", "output": "bab"}],
                    "test_cases": [
                        {"input": "babad", "expected_output": "bab", "is_hidden": False},
                        {"input": "cbbd", "expected_output": "bb", "is_hidden": True},
                    ]
                }
            ]
        }

_seed_default_question_bank()


# ---------------------------------------------------------------------------
# DemoStore API
# ---------------------------------------------------------------------------
class DemoStore:
    """Static helper class — all methods are class-level, no instantiation."""

    # ── Question Banks ───────────────────────────────────────────────────

    @classmethod
    def save_question_bank(cls, bank_data: dict) -> dict:
        bank_id = bank_data.get("id") or str(uuid.uuid4())
        bank = {
            "id": bank_id,
            "title": bank_data.get("title", "Uploaded Question Bank"),
            "topic": bank_data.get("topic", "General"),
            "description": bank_data.get("description", ""),
            "created_at": datetime.utcnow().isoformat(),
            "questions": bank_data.get("questions", []),
        }
        _question_banks[bank_id] = bank
        return bank

    @classmethod
    def get_question_banks(cls) -> List[dict]:
        return list(_question_banks.values())

    @classmethod
    def get_question_bank(cls, bank_id: str) -> Optional[dict]:
        return _question_banks.get(bank_id)

    # ── Assessments ───────────────────────────────────────────────────────

    @classmethod
    def create_assessment(cls, data: dict) -> dict:
        assessment_id = str(uuid.uuid4())
        assessment = {
            "id": assessment_id,
            "title": data["title"],
            "description": data.get("description", ""),
            "duration_minutes": data["duration_minutes"],
            "language": data.get("language", "Python"),
            "topic": data.get("topic", "Algorithms"),
            "difficulty_distribution": data.get("difficulty_distribution", {"EASY": 0, "MEDIUM": 0, "HARD": 0}),
            "total_questions": data.get("total_questions", 0),
            "questions": data.get("questions", []),   # list of question dicts
            "status": "CONFIRMED",
            "created_at": datetime.utcnow().isoformat(),
        }
        _assessments[assessment_id] = assessment
        return assessment

    @classmethod
    def get_assessment(cls, assessment_id: str) -> Optional[dict]:
        return _assessments.get(assessment_id)

    @classmethod
    def get_assessments(cls) -> List[dict]:
        return list(_assessments.values())

    @classmethod
    def update_assessment_questions(cls, assessment_id: str, questions: list) -> Optional[dict]:
        if assessment_id not in _assessments:
            return None
        _assessments[assessment_id]["questions"] = questions
        _assessments[assessment_id]["total_questions"] = len(questions)
        return _assessments[assessment_id]

    # ── Assignments ───────────────────────────────────────────────────────

    @classmethod
    def assign_assessment(cls, assessment_id: str, intern_email: str) -> dict:
        assignment_id = str(uuid.uuid4())
        assignment = {
            "id": assignment_id,
            "assessment_id": assessment_id,
            "intern_email": intern_email,
            "status": "ASSIGNED",
            "assigned_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "submitted_at": None,
        }
        _assignments[assignment_id] = assignment
        # Also index by intern email for fast lookup
        _assignments[f"email:{intern_email}"] = assignment
        return assignment

    @classmethod
    def get_intern_assignment(cls, intern_email: str) -> Optional[dict]:
        return _assignments.get(f"email:{intern_email}")

    @classmethod
    def start_assignment(cls, intern_email: str) -> Optional[dict]:
        assignment = cls.get_intern_assignment(intern_email)
        if assignment and not assignment.get("started_at"):
            assignment["started_at"] = datetime.utcnow().isoformat()
            assignment["status"] = "IN_PROGRESS"
        return assignment

    # ── Submissions ───────────────────────────────────────────────────────

    @classmethod
    def save_submission(cls, data: dict) -> dict:
        submission_id = str(uuid.uuid4())
        submitted_at = datetime.utcnow().isoformat()
        submission = {
            "id": submission_id,
            "assignment_id": data.get("assignment_id"),
            "assessment_id": data.get("assessment_id"),
            "intern_email": data.get("intern_email"),
            "code_by_question": data.get("code_by_question", {}),   # question_id -> {language, code}
            "final_language": data.get("final_language", "python"),
            "submitted_at": submitted_at,
            "status": "SUBMITTED",
            "gemini_review_status": "PENDING",
        }
        _submissions[submission_id] = submission

        # Mark assignment as submitted
        intern_email = data.get("intern_email", "")
        assignment = cls.get_intern_assignment(intern_email)
        if assignment:
            assignment["submitted_at"] = submitted_at
            assignment["status"] = "COMPLETED"

        return submission

    @classmethod
    def get_submission(cls, submission_id: str) -> Optional[dict]:
        return _submissions.get(submission_id)

    @classmethod
    def get_submissions(cls) -> List[dict]:
        """Return only submitted (completed) entries."""
        return [s for s in _submissions.values() if s.get("status") == "SUBMITTED"]

    @classmethod
    def get_submission_for_intern(cls, intern_email: str) -> Optional[dict]:
        for s in _submissions.values():
            if s.get("intern_email") == intern_email and s.get("status") == "SUBMITTED":
                return s
        return None

    # ── Judge0 Results ────────────────────────────────────────────────────

    @classmethod
    def save_judge_result(cls, run_id: str, results: list) -> None:
        _judge_results[run_id] = results

    @classmethod
    def get_judge_results(cls, run_id: str) -> List[dict]:
        return _judge_results.get(run_id, [])

    # ── Gemini Reviews ────────────────────────────────────────────────────

    @classmethod
    def save_gemini_review(cls, submission_id: str, review: dict) -> None:
        _gemini_reviews[submission_id] = review
        if submission_id in _submissions:
            _submissions[submission_id]["gemini_review_status"] = "COMPLETED"

    @classmethod
    def get_gemini_review(cls, submission_id: str) -> Optional[dict]:
        return _gemini_reviews.get(submission_id)

    # ── Demo Reset ────────────────────────────────────────────────────────

    # ── Authority Decisions ───────────────────────────────────────────────

    @classmethod
    def save_decision(cls, submission_id: str, decision: dict) -> dict:
        """Save authority decision for a submission."""
        _decisions[submission_id] = decision
        return decision

    @classmethod
    def get_decision(cls, submission_id: str) -> Optional[dict]:
        return _decisions.get(submission_id)

    # ── Demo Reset ────────────────────────────────────────────────────────

    @classmethod
    def reset(cls) -> None:
        """Clear all demo state and restore initial conditions."""
        _assessments.clear()
        _assignments.clear()
        _submissions.clear()
        _gemini_reviews.clear()
        _judge_results.clear()
        _decisions.clear()

    # ── Stats ─────────────────────────────────────────────────────────────

    @classmethod
    def get_dashboard_stats(cls) -> dict:
        assessments = cls.get_assessments()
        submissions = cls.get_submissions()
        pending_reviews = [s for s in submissions if s.get("gemini_review_status") != "COMPLETED"]
        return {
            "active_assessments": len(assessments),
            "candidates": 1,   # demo always has intern@test.com
            "submissions_count": len(submissions),
            "pending_reviews": len(pending_reviews),
            "recent_assessments": [
                {
                    "id": a["id"],
                    "title": a["title"],
                    "questions": a.get("total_questions", 0),
                    "interns": 1 if any(
                        asg for asg in _assignments.values()
                        if isinstance(asg, dict) and asg.get("assessment_id") == a["id"]
                        and not asg.get("intern_email", "").startswith("email:")
                    ) else 0,
                    "status": a["status"],
                    "created_at": a["created_at"],
                    "deadline_at": None,
                }
                for a in assessments
            ],
            "candidate_activity": cls._build_candidate_activity(),
        }

    @classmethod
    def _build_candidate_activity(cls) -> list:
        activities = []
        for s in _submissions.values():
            if s.get("submitted_at"):
                assessment = _assessments.get(s.get("assessment_id", ""))
                activities.append({
                    "intern_name": s["intern_email"].split("@")[0],
                    "assessment_title": assessment["title"] if assessment else "Assessment",
                    "action": "submitted",
                    "timestamp": s["submitted_at"],
                })
        return activities[-5:]   # last 5
