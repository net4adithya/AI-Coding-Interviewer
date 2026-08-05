# python_backend/app/routers/audit.py
"""Audit router placeholder."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_audit():
    return {"msg": "audit router active"}
