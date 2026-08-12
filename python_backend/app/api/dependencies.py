# python_backend/app/api/dependencies.py
"""Centralized FastAPI dependencies for authentication and RBAC."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.session import SessionLocal
from app.config import settings
from app.users.models import User, RoleEnum
import requests
from threading import Lock

_bearer_scheme = HTTPBearer(auto_error=False)

JWKS = None
JWKS_LOCK = Lock()

def get_jwks():
    global JWKS
    if JWKS is None:
        with JWKS_LOCK:
            if JWKS is None:
                try:
                    project_ref = settings.DATABASE_URL.split("postgres.")[1].split(":")[0]
                except Exception:
                    project_ref = "rfqmnstrnvipxknvrouy"
                jwks_url = f"https://{project_ref}.supabase.co/auth/v1/.well-known/jwks.json"
                res = requests.get(jwks_url)
                if res.status_code == 200:
                    JWKS = res.json()
                else:
                    JWKS = settings.JWT_SECRET # fallback to symmetric key if jwks fails
    return JWKS

def get_db():
    """Yield a SQLAlchemy session and ensure it is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Verify Supabase JWT, ensure local User exists, and return it."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required."
        )

    token = credentials.credentials
    try:
        from jose import jwt
        
        # LOG THE UNVERIFIED HEADER
        try:
            unverified_header = jwt.get_unverified_header(token)
            print(f"DEBUG TOKEN HEADER: {unverified_header}", flush=True)
        except Exception as e:
            print(f"DEBUG FAILED TO PARSE HEADER: {e}", flush=True)

        # Supabase uses JWKS for asymmetric signing
        payload = jwt.decode(
            token, 
            get_jwks() or settings.JWT_SECRET, 
            algorithms=["ES256", "RS256", "HS256"],
            options={"verify_aud": False}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}"
        )

    supabase_uid = payload.get("sub")
    email = payload.get("email", "")
    
    # Use user_metadata role or default to intern for new users
    user_metadata = payload.get("user_metadata", {})
    token_role = user_metadata.get("role", "intern").lower()

    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain a valid subject (user id)."
        )

    # Map to local user
    user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
    
    if not user:
        # Provision new user on first login
        try:
            role = RoleEnum(token_role)
        except ValueError:
            role = RoleEnum.INTERN
            
        user = User(
            supabase_uid=supabase_uid,
            email=email,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user

def get_current_user_context(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Compatibility dependency for older routers expecting a context dict."""
    return {
        "user_id": user.id,
        "role": user.role.value
    }

def require_authority(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Ensure the user is an Authority."""
    if user.role not in [RoleEnum.AUTHORITY, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires AUTHORITY role."
        )
    return {"user_id": user.id, "role": user.role.value}

def require_intern(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Ensure the user is an Intern."""
    if user.role not in [RoleEnum.INTERN, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires INTERN role."
        )
    return {"user_id": user.id, "role": user.role.value}
