# python_backend/app/routers/dashboard.py
"""Dashboard router placeholder."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_dashboard():
    return {"msg": "dashboard router active"}
