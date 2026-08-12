# python_backend/app/users/models.py
"""SQLAlchemy models for Users."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Index
import enum

from app.db.base_class import Base

class RoleEnum(str, enum.Enum):
    AUTHORITY = "authority"
    INTERN = "intern"
    ADMIN = "admin"

class User(Base):
    """Local user record mapped from Supabase authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supabase_uid = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.INTERN)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
