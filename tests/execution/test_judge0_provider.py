# tests/execution/test_judge0_provider.py
"""Tests for Judge0ExecutionProvider using mocked httpx client."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.execution.providers.judge0_provider import Judge0ExecutionProvider
from app.execution.providers.base import ExecutionRequest
from app.execution.exceptions import (
    ExecutionProviderUnavailableError,
    ExecutionTimeoutError,
    ExecutionRateLimitedError,
)


@pytest.fixture()
def provider():
    return Judge0ExecutionProvider(
        api_url="https://mock.judge0.com",
        api_key="mock_secret_key",
        timeout=5.0,
        poll_interval=0.01,
        max_poll_attempts=3,
    )


@pytest.fixture()
def req():
    return ExecutionRequest(
        submission_id=1,
        test_case_id=1,
        language="python",
        source_code="print('hello')",
        stdin="",
        expected_output="hello\n",
    )


def test_successful_submit_and_poll(provider, req):
    async def _test():
        submit_response = MagicMock()
        submit_response.status_code = 201
        submit_response.json.return_value = {"token": "token-123"}

        poll_response = MagicMock()
        poll_response.status_code = 200
        poll_response.json.return_value = {
            "token": "token-123",
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "hello\n",
            "stderr": None,
            "compile_output": None,
            "time": "0.05",
            "memory": 12000,
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = submit_response
        mock_client.get.return_value = poll_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            mock_client.__aenter__.return_value = mock_client
            result = await provider.execute(req)

        assert result.token == "token-123"
        assert result.status_id == 3
        assert result.stdout == "hello\n"
        assert result.execution_time == 0.05
        assert result.memory == 12000

    asyncio.run(_test())


def test_compilation_error(provider, req):
    async def _test():
        submit_resp = MagicMock(status_code=201, json=lambda: {"token": "tok-ce"})
        poll_resp = MagicMock(
            status_code=200,
            json=lambda: {
                "token": "tok-ce",
                "status": {"id": 6, "description": "Compilation Error"},
                "compile_output": "SyntaxError: invalid syntax",
            },
        )
        mock_client = AsyncMock()
        mock_client.post.return_value = submit_resp
        mock_client.get.return_value = poll_resp

        with patch("httpx.AsyncClient", return_value=mock_client):
            mock_client.__aenter__.return_value = mock_client
            res = await provider.execute(req)

        assert res.status_id == 6
        assert "SyntaxError" in res.compile_output

    asyncio.run(_test())


def test_rate_limit_handling(provider, req):
    async def _test():
        resp = MagicMock(status_code=429)
        mock_client = AsyncMock()
        mock_client.post.return_value = resp

        with patch("httpx.AsyncClient", return_value=mock_client):
            mock_client.__aenter__.return_value = mock_client
            with pytest.raises(ExecutionRateLimitedError):
                await provider.submit(req)

    asyncio.run(_test())


def test_provider_500_error(provider, req):
    async def _test():
        resp = MagicMock(status_code=500)
        mock_client = AsyncMock()
        mock_client.post.return_value = resp

        with patch("httpx.AsyncClient", return_value=mock_client):
            mock_client.__aenter__.return_value = mock_client
            with pytest.raises(ExecutionProviderUnavailableError):
                await provider.submit(req)

    asyncio.run(_test())


def test_timeout_handling(provider, req):
    async def _test():
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")

        with patch("httpx.AsyncClient", return_value=mock_client):
            mock_client.__aenter__.return_value = mock_client
            with pytest.raises(ExecutionTimeoutError):
                await provider.submit(req)

    asyncio.run(_test())
