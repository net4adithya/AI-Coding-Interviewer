# python_backend/app/routers/assignments.py
"""Assignments router placeholder."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_assignments():
    return {"msg": "assignments router active"}
