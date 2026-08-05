# python_backend/app/routers/interns.py
"""Interns router placeholder."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_interns():
    return {"msg": "interns router active"}
