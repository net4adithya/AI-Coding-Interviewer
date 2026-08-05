# python_backend/app/routers/users.py
"""Users router placeholder."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_users():
    return {"msg": "users router active"}
