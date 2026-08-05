# python_backend/app/routers/roles.py
"""Roles router placeholder."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_roles():
    return {"msg": "roles router active"}
