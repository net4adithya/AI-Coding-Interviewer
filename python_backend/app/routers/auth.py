# python_backend/app/routers/auth.py
"""Auth router placeholder."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_auth():
    return {"msg": "auth router active"}
