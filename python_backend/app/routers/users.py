# python_backend/app/routers/users.py
"""Users router for profile management."""

from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.users.models import User
from app.users.schemas import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current user's profile based on the authoritative local database."""
    return {
        "id": current_user.id,
        "supabase_uid": current_user.supabase_uid,
        "email": current_user.email,
        "role": current_user.role.value
    }
