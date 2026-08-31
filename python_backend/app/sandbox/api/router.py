"""FastAPI routes for Docker sandbox execution."""

from fastapi import APIRouter, HTTPException, status

from app.sandbox.config import sandbox_settings
from app.sandbox.queue import ExecutionQueue
from app.sandbox.schemas import ExecutionRequest, ExecutionResponse, ExecutionStatus

router = APIRouter()


@router.get("/health")
def sandbox_health():
    queue = ExecutionQueue()
    redis_ok = False
    try:
        redis_ok = queue.ping()
    except Exception:
        redis_ok = False
    return {
        "status": "ok" if redis_ok and sandbox_settings.SANDBOX_ENABLED else "degraded",
        "sandbox_enabled": sandbox_settings.SANDBOX_ENABLED,
        "redis": redis_ok,
        "queue": sandbox_settings.EXECUTION_QUEUE_KEY,
    }


@router.post("/run", response_model=ExecutionResponse)
def run_code(request: ExecutionRequest) -> ExecutionResponse:
    """Enqueue an execution job and wait for the worker result."""
    if not sandbox_settings.SANDBOX_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sandbox execution is disabled.",
        )

    queue = ExecutionQueue()
    try:
        if not queue.ping():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis is not available.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection failed: {exc}",
        ) from exc

    job_id = queue.enqueue(request.model_dump())
    result = queue.wait_for_result(job_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Execution timed out waiting for worker. Is the sandbox worker running?",
        )

    result.job_id = job_id
    return result
