# python_backend/app/execution/tasks/execution_tasks.py
"""Asynchronous task processor implementing Phase 7's SubmissionProcessingInterface."""

import asyncio
import logging
import threading

from app.editor.tasks import SubmissionProcessingInterface
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _run_async_pipeline(submission_id: int):
    """Worker function executing the execution pipeline in an event loop."""
    from app.execution.services.execution_service import ExecutionService

    logger.info("[Judge0SubmissionProcessor] Background execution starting for submission %d", submission_id)
    db = SessionLocal()
    try:
        service = ExecutionService(db=db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(service.run_execution_pipeline(submission_id))
        loop.close()
        logger.info("[Judge0SubmissionProcessor] Background execution completed for submission %d", submission_id)
    except Exception as exc:
        logger.error("[Judge0SubmissionProcessor] Background execution error for submission %d: %s", submission_id, exc)
    finally:
        db.close()


class Judge0SubmissionProcessor(SubmissionProcessingInterface):
    """Concrete SubmissionProcessingInterface that launches Phase 8 execution in a background thread."""

    def trigger(self, submission_id: int) -> None:
        logger.info(
            "[Judge0SubmissionProcessor] Received submission %d trigger. Dispatching background thread.",
            submission_id,
        )
        thread = threading.Thread(
            target=_run_async_pipeline,
            args=(submission_id,),
            daemon=True,
        )
        thread.start()
