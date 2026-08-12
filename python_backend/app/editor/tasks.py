# python_backend/app/editor/tasks.py
"""Background task abstraction for post-submission processing.

The editor module does NOT implement Judge0, Gemini, or Static Analysis.
It only provides a thin interface to trigger the existing (or future)
processing pipeline after a final submission is created.

The FastAPI BackgroundTasks mechanism is used here so the HTTP response
is returned immediately while the processing pipeline runs asynchronously.
A Phase 8 implementation can replace `_run_submission_pipeline` with a
Celery task, RQ job, or any other queuing backend without changing the
editor service.
"""

import logging

logger = logging.getLogger(__name__)


class SubmissionProcessingInterface:
    """Abstract contract for triggering post-submission analysis.

    The editor service depends on this interface, not on any concrete
    implementation.  Phase 8 will provide a concrete implementation backed
    by Judge0 / Celery / etc.
    """

    def trigger(self, submission_id: int) -> None:  # pragma: no cover
        raise NotImplementedError


class LoggingSubmissionProcessor(SubmissionProcessingInterface):
    """Default no-op processor that logs a message.

    Used in Phase 7 until Phase 8 provides a real execution engine.
    Replace this by registering a different SubmissionProcessingInterface
    implementation in the dependency injection layer.
    """

    def trigger(self, submission_id: int) -> None:
        logger.info(
            "[EditorTasks] Submission %d queued for processing. "
            "Connect Phase 8 execution engine to process it.",
            submission_id,
        )


def get_submission_processor() -> SubmissionProcessingInterface:
    """Factory function consumed by FastAPI Depends().

    Returns a LoggingSubmissionProcessor for now.  Phase 8 can override
    this dependency with a real implementation.
    """
    return LoggingSubmissionProcessor()
