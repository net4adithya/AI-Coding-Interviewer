import pytest
from ai_review.utils.retry_handler import RetryHandler, NonRetryableError

def test_retry_handler_success_first_try():
    handler = RetryHandler(max_attempts=3, initial_delay=0.01)
    call_count = 0
    def _func():
        nonlocal call_count
        call_count += 1
        return "OK"
    res = handler.execute(_func)
    assert res == "OK"
    assert call_count == 1

def test_retry_handler_transient_failure_then_success():
    handler = RetryHandler(max_attempts=3, initial_delay=0.01)
    call_count = 0
    def _func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("Temporary 500 error")
        return "SUCCESS"
    res = handler.execute(_func)
    assert res == "SUCCESS"
    assert call_count == 2

def test_retry_handler_non_retryable_auth_error():
    handler = RetryHandler(max_attempts=3, initial_delay=0.01)
    call_count = 0
    def _func():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("401 Unauthorized - Invalid API Key")
    with pytest.raises(NonRetryableError):
        handler.execute(_func)
    assert call_count == 1
