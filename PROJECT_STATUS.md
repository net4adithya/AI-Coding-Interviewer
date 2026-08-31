# AI Coding Interviewer — Project Status

## Current Stage
Stage 2 — Docker Execution Engine Foundation

## Product Goal
An online coding assessment platform where an admin creates assessments from question banks, publishes them, candidates enter a test using an access code, solve coding questions in Monaco, code is securely executed in a sandbox, submissions are reviewed by Gemini, and admins review execution + AI results.

## Current Architecture
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS (`frontend/`)
- **Backend**: FastAPI (`python_backend/main.py`) with production PostgreSQL routes and a parallel in-memory **demo mode** (`/demo/*`)
- **Execution (new)**: Docker sandbox + Redis queue + worker (`python_backend/app/sandbox/`)
- **Execution (legacy, retained)**: Judge0 via demo router and production `/api/v1/execution/*`

## Frontend
- **Framework**: React 18, TypeScript, Vite 5, Tailwind CSS
- **Entry**: `frontend/src/main.tsx` → `App.tsx` → `router/index.tsx`
- **Monaco workspace**: `/intern/interview/workspace` — `frontend/src/pages/intern/Workspace.tsx`
- **Execution integration**: `frontend/src/services/workspaceExecution.ts`
  - Primary: `POST /api/v1/sandbox/execution/run` (Docker sandbox)
  - Fallback: `demoService.runCode` / `runTestCases` (Judge0/demo) when sandbox unavailable
  - Toggle: `VITE_SANDBOX_EXECUTION=false` disables sandbox attempts
- **Languages**: Python (default), Java, C++, JavaScript

## Backend
- **Sandbox API** (no DB): `/api/v1/sandbox/execution/run`, `/health`
- **Demo API**: `/demo/*` — in-memory store, Judge0 execution (unchanged)
- **Production execution API**: `/api/v1/execution/*` — Judge0 post-submission (unchanged)

## Database
Database integration intentionally deferred during current implementation stage.

## Execution

### Stage 2 — Docker Execution Engine

| Item | Status |
|------|--------|
| **Redis** | Configured via `docker-compose.yml` (`redis:7-alpine` on port 6379) |
| **Docker** | Worker uses official images: `python:3.12-slim`, `node:20-alpine`, `gcc:13`, `eclipse-temurin:17-jdk` |
| **Worker** | `python -m app.sandbox.worker` (or `sandbox-worker` compose service) |
| **Endpoint** | `POST /api/v1/sandbox/execution/run` |
| **Queue key** | `sandbox:execution:jobs` |

**Request format:**
```json
{
  "question_id": "...",
  "language": "python",
  "source_code": "...",
  "stdin": "..."
}
```

**Response format:**
```json
{
  "job_id": "uuid",
  "status": "ACCEPTED | RUNTIME_ERROR | TIME_LIMIT_EXCEEDED | COMPILATION_ERROR | INTERNAL_ERROR",
  "stdout": "...",
  "stderr": "...",
  "exit_code": 0,
  "execution_time_ms": 123,
  "memory_kb": 0
}
```

**Architecture:**
```
Frontend → workspaceExecution.ts → POST /api/v1/sandbox/execution/run
  → Redis queue → sandbox worker → Docker container → result stored in Redis → API returns
```

**Resource limits (server-enforced):**
- Memory: 256 MB (`EXECUTION_MEMORY_MB`)
- CPU: 1 core (`EXECUTION_CPUS`)
- Timeout: 10 s per execution (`EXECUTION_TIMEOUT_SEC`)
- Network: disabled (`network_mode=none`)
- Capabilities: `cap_drop=ALL`, `no-new-privileges`
- User: `nobody` inside container
- Temp dir: host `tempfile.mkdtemp`, deleted after run; container removed with `force=True`

**Security restrictions:**
- Candidate code never runs on FastAPI host process
- No Docker socket inside execution containers
- No privileged mode
- No candidate-controlled image/volume/network/CPU/memory settings
- Source/stdin/output size limits enforced

**Files created/modified (Stage 2):**
- `python_backend/app/sandbox/` — config, schemas, executor, queue, worker, API router
- `python_backend/main.py` — mount sandbox router
- `python_backend/requirements.txt` — `redis`, `docker`
- `python_backend/Dockerfile.sandbox-worker`
- `docker-compose.yml` — Redis + worker
- `frontend/src/services/workspaceExecution.ts` — sandbox primary, Judge0 fallback
- `tests/sandbox/` — unit + Docker integration tests
- `.env.example` — sandbox env vars

**Known limitations (Stage 2):**
- Single worker only (no horizontal scaling yet)
- `memory_kb` not populated from Docker stats yet
- Test-case batch runs sequentially (no hidden-test evaluation)
- Worker container needs host Docker socket (for local dev only; production needs secure worker deployment)
- Judge0/demo path still present as fallback
- Requires Docker Desktop/daemon running for sandbox execution

### Legacy execution (retained)
- Demo: `python_backend/app/demo/judge0_service.py` (Judge0 + local subprocess fallback)
- Production: `python_backend/app/execution/` (Judge0 post-submission pipeline)

## AI
- Gemini configured but unchanged in Stage 2
- Post-submit code review via demo `gemini_service.py`
- Production `ai_review` router still not mounted

## Authentication
- Unchanged — demo tokens or Supabase JWT
- Sandbox `/run` endpoint has no auth in Stage 2 (add before production)

## Known Issues
- Workspace loads assessment via `demoService.getMyAssignment()` (email assignment)
- No access-code candidate flow
- Sandbox endpoint not authenticated
- Admin review does not show sandbox execution results yet

## Completed in Stage 1
- Monaco workspace, per-question/per-language state, execution request contract

## Completed in Stage 2
- Docker sandbox executor with Redis job queue and worker
- Judge0-independent execution contract
- Frontend abstraction with fallback
- docker-compose for Redis + worker
- Focused unit and integration tests

## Local Development Commands

```bash
# 1. Redis
docker compose up redis -d

# 2. Execution worker (from python_backend/, with venv active)
python -m app.sandbox.worker

# 3. FastAPI (from python_backend/)
uvicorn main:app --reload --port 8000

# 4. Frontend (from frontend/)
npm run dev
```

Optional: `docker compose up -d` starts Redis + worker container (requires Docker socket mount).

## Next Recommended Stage
Wire sandbox execution into submission persistence and replace demo/Judge0 run path entirely; add candidate access-code flow.
