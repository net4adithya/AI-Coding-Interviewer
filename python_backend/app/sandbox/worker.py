"""Sandbox execution worker — consumes Redis jobs and runs Docker sandbox."""

from __future__ import annotations

import logging
import signal
import sys

from app.sandbox.executor import DockerSandboxExecutor, UnsupportedLanguageError
from app.sandbox.queue import ExecutionQueue
from app.sandbox.schemas import ExecutionResponse, ExecutionStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sandbox.worker")

_running = True


def _handle_signal(signum, frame):
    global _running
    logger.info("Received signal %s, shutting down worker...", signum)
    _running = False


def process_job(job: dict, executor: DockerSandboxExecutor, queue: ExecutionQueue) -> None:
    job_id = job["job_id"]
    language = job.get("language", "")
    source_code = job.get("source_code", "")
    stdin = job.get("stdin", "")
    question_id = job.get("question_id")

    logger.info("[Worker] Processing job %s language=%s", job_id, language)

    try:
        result = executor.execute(
            language=language,
            source_code=source_code,
            stdin=stdin,
            question_id=question_id,
        )
    except UnsupportedLanguageError as exc:
        result = ExecutionResponse(
            job_id=job_id,
            status=ExecutionStatus.INTERNAL_ERROR,
            stderr=str(exc),
            exit_code=-1,
        )
    except Exception as exc:
        logger.exception("[Worker] Job %s failed", job_id)
        result = ExecutionResponse(
            job_id=job_id,
            status=ExecutionStatus.INTERNAL_ERROR,
            stderr=str(exc),
            exit_code=-1,
        )

    result.job_id = job_id
    queue.set_result(job_id, result)
    logger.info("[Worker] Job %s completed status=%s", job_id, result.status.value)


def main() -> int:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    queue = ExecutionQueue()
    executor = DockerSandboxExecutor()

    try:
        queue.ping()
    except Exception as exc:
        logger.error("Cannot connect to Redis: %s", exc)
        return 1

    logger.info("Sandbox execution worker started. Waiting for jobs...")

    while _running:
        job = queue.blocking_pop_job(timeout_sec=3)
        if not job:
            continue
        process_job(job, executor, queue)

    logger.info("Worker stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
