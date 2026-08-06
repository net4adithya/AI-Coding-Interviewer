import time
import logging
from typing import Callable, Any

logger = logging.getLogger("ai_review.retry_handler")

class NonRetryableError(Exception):
    """Errors that should NOT be retried (e.g. Invalid API Key, Auth failure)."""
    pass

class RetryHandler:
    """Executes callables with exponential backoff up to max_attempts."""

    def __init__(self, max_attempts: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor

    def execute(self, func: Callable[[], Any]) -> Any:
        attempt = 0
        delay = self.initial_delay
        last_exception = None

        while attempt < self.max_attempts:
            attempt += 1
            try:
                return func()
            except NonRetryableError as nre:
                logger.error(f"Non-retryable error on attempt {attempt}: {nre}")
                raise nre
            except Exception as exc:
                last_exception = exc
                err_msg = str(exc).lower()

                # Check for non-retryable status codes / keywords
                if "invalid api key" in err_msg or "unauthorized" in err_msg or "401" in err_msg or "403" in err_msg:
                    logger.error(f"Authentication/Authorization error encountered: {exc}")
                    raise NonRetryableError(f"Authentication failure: {exc}") from exc

                if attempt >= self.max_attempts:
                    logger.error(f"Max retry attempts ({self.max_attempts}) reached. Failing with: {exc}")
                    raise exc

                logger.warning(f"Attempt {attempt} failed: {exc}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= self.backoff_factor

        raise last_exception
