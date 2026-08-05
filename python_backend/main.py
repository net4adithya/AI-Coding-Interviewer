# python_backend/main.py

"""Entry point for the FastAPI backend.

This skeleton mirrors the NestJS application structure, exposing similar routes
and reading configuration from the same `.env` file. It uses SQLAlchemy for the
ORM and Pydantic models for request validation.
"""

import uvicorn
from fastapi import FastAPI
from app.config import settings
from app.routers import auth, users, roles, authorities, interns, assignments, dashboard, audit, submissions

app = FastAPI(
    title="AI Coding Review Platform API",
    description="Backend API for AI Coding Review Platform (Phase 1)",
    version="1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Include routers – each router mirrors a NestJS module.
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(roles.router, prefix="/roles", tags=["roles"])
app.include_router(authorities.router, prefix="/authorities", tags=["authorities"])
app.include_router(interns.router, prefix="/interns", tags=["interns"])
app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(audit.router, prefix="/audit-logs", tags=["audit"])
app.include_router(submissions.router, prefix="/submissions", tags=["submissions"])

# Root health endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(settings.PORT), reload=True)
