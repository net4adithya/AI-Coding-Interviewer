# python_backend/main.py

"""Entry point for the FastAPI backend.

This skeleton mirrors the NestJS application structure, exposing similar routes
and reading configuration from the same `.env` file. It uses SQLAlchemy for the
ORM and Pydantic models for request validation.

DEMO_MODE=true:
  - Adds /demo/* router (in-memory store, no PostgreSQL)
  - Skips PostgreSQL-dependent routers if DB is unavailable
  - Uses real Judge0 and real Gemini APIs
"""

import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Add root directory to sys.path so modules like static_analysis, ai_review,
# and authority_review can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")

app = FastAPI(
    title="AI Coding Review Platform API",
    description="Backend API for AI Coding Review Platform",
    version="1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Sandbox execution (Docker + Redis, no DB required) ────────────────────────
from app.sandbox.api.router import router as sandbox_execution_router

app.include_router(
    sandbox_execution_router,
    prefix="/api/v1/sandbox/execution",
    tags=["sandbox-execution"],
)

# ── Demo Mode Router (no DB required) ─────────────────────────────────────────
if DEMO_MODE:
    from app.demo.router import router as demo_router
    app.include_router(demo_router, prefix="/demo", tags=["demo"])
    print("=" * 60)
    print("  DEMO MODE ENABLED — No PostgreSQL required")
    print("  Admin:  admin@test.com  /  demo123")
    print("  Intern: intern@test.com /  demo123")
    print("  Demo API: /demo/*")
    print("=" * 60)

# ── Production Routers (gracefully skip if DB unavailable) ────────────────────
_db_routers_loaded = False

try:
    import importlib
    # Dynamic imports so module-level syntax errors/missing packages don't crash us
    auth = importlib.import_module("app.routers.auth")
    users = importlib.import_module("app.routers.users")
    roles = importlib.import_module("app.routers.roles")
    authorities = importlib.import_module("app.routers.authorities")
    interns = importlib.import_module("app.routers.interns")
    assignments = importlib.import_module("app.routers.assignments")
    dashboard = importlib.import_module("app.routers.dashboard")
    audit = importlib.import_module("app.routers.audit")
    submissions = importlib.import_module("app.routers.submissions")
    static_analysis_mod = importlib.import_module("static_analysis.api.router")
    authority_review_mod = importlib.import_module("authority_review.api.router")
    editor_mod = importlib.import_module("app.editor.api.router")
    execution_mod = importlib.import_module("app.execution.api.router")
    assessment_mod = importlib.import_module("app.assessment.api.router")

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(roles.router, prefix="/roles", tags=["roles"])
    app.include_router(authorities.router, prefix="/authorities", tags=["authorities"])
    app.include_router(interns.router, prefix="/interns", tags=["interns"])
    app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(audit.router, prefix="/audit-logs", tags=["audit"])
    app.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
    app.include_router(static_analysis_mod.router, prefix="/static-analysis", tags=["static-analysis"])
    app.include_router(authority_review_mod.router, prefix="/authority-review", tags=["authority-review"])
    app.include_router(editor_mod.router, prefix="/api/v1/editor", tags=["editor"])
    app.include_router(execution_mod.router, prefix="/api/v1/execution", tags=["execution"])
    app.include_router(assessment_mod.router, prefix="/api/v1/assessments", tags=["assessments"])
    _db_routers_loaded = True

except Exception as e:
    if DEMO_MODE:
        print(f"[INFO] Production DB routers not loaded (demo mode active, this is expected): {e}")
    else:
        # In production mode, re-raise so the issue is visible
        raise



# Root health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "demo_mode": DEMO_MODE,
        "db_routers": _db_routers_loaded,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(settings.PORT), reload=True)
