# python_backend/app/routers/submissions.py
"""Submissions router placeholder."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_submissions():
    return {"msg": "submissions router active"}
