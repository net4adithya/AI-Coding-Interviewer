# python_backend/app/routers/authorities.py
"""Authorities router placeholder."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_authorities():
    return {"msg": "authorities router active"}
