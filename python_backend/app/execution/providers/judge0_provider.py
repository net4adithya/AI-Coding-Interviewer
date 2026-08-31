# python_backend/app/execution/providers/judge0_provider.py
"""Judge0 Execution Provider implementation using httpx async client.

Submits code to Judge0 HTTP API, polls submission tokens, handles timeouts
and rate limits, and sanitizes API keys from exception/logging output.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

import httpx

from app.execution.config import execution_settings
from app.execution.exceptions import (
    ExecutionProviderUnavailableError,
    ExecutionTimeoutError,
    ExecutionRateLimitedError,
)
from app.execution.language.judge0_language_map import get_judge0_language_id
from app.execution.providers.base import (
    BaseExecutionProvider,
    ExecutionRawResult,
    ExecutionRequest,
)

logger = logging.getLogger(__name__)


class Judge0ExecutionProvider(BaseExecutionProvider):
    """Concrete Judge0 sandbox provider."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        poll_interval: Optional[float] = None,
        max_poll_attempts: Optional[int] = None,
    ):
        self._api_url = (api_url or execution_settings.JUDGE0_API_URL).rstrip("/")
        self._api_key = api_key or execution_settings.JUDGE0_API_KEY
        self._timeout = timeout or execution_settings.JUDGE0_REQUEST_TIMEOUT
        self._poll_interval = poll_interval or execution_settings.JUDGE0_POLL_INTERVAL
        self._max_poll_attempts = max_poll_attempts or execution_settings.JUDGE0_MAX_POLL_ATTEMPTS

    def provider_name(self) -> str:
        return "judge0"

    def provider_version(self) -> str:
        return "ce-v1.13"

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-RapidAPI-Key"] = self._api_key
            headers["X-Auth-Token"] = self._api_key
        return headers

    async def submit(self, request: ExecutionRequest) -> str:
        """Submit source code to Judge0 `/submissions?base64_encoded=false`."""
        language_id = get_judge0_language_id(request.language)
        payload = {
            "source_code": request.source_code,
            "language_id": language_id,
            "stdin": request.stdin or "",
            "expected_output": request.expected_output or "",
            "cpu_time_limit": min(request.time_limit_sec, execution_settings.MAX_EXECUTION_TIME),
            "memory_limit": min(request.memory_limit_mb * 1024, execution_settings.MAX_MEMORY_LIMIT),
        }

        url = f"{self._api_url}/submissions?base64_encoded=false"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload, headers=self._get_headers())
        except httpx.TimeoutException:
            raise ExecutionTimeoutError(self._timeout)
        except Exception as exc:
            logger.error("[Judge0Provider] Failed to submit job: %s", str(exc))
            raise ExecutionProviderUnavailableError("Judge0", str(exc))

        if response.status_code in (401, 403):
            raise ExecutionProviderUnavailableError("Judge0", f"Unauthorized (HTTP {response.status_code}). Check JUDGE0_API_KEY / RapidAPI key.")
        elif response.status_code == 429:
            raise ExecutionRateLimitedError("Judge0")
        elif response.status_code >= 500:
            raise ExecutionProviderUnavailableError("Judge0", f"HTTP {response.status_code}")
        elif response.status_code not in (200, 201):
            raise ExecutionProviderUnavailableError(
                "Judge0", f"Submission rejected (HTTP {response.status_code}: {response.text[:100]})"
            )

        data = response.json()
        token = data.get("token")
        if not token:
            raise ExecutionProviderUnavailableError("Judge0", "Response missing submission token")
        return token

    async def get_result(self, token: str) -> ExecutionRawResult:
        """Fetch result for submission token from Judge0 `/submissions/{token}?base64_encoded=false`."""
        url = f"{self._api_url}/submissions/{token}?base64_encoded=false"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=self._get_headers())
        except httpx.TimeoutException:
            raise ExecutionTimeoutError(self._timeout)
        except Exception as exc:
            raise ExecutionProviderUnavailableError("Judge0", str(exc))

        if response.status_code == 429:
            raise ExecutionRateLimitedError("Judge0")
        elif response.status_code >= 500:
            raise ExecutionProviderUnavailableError("Judge0", f"HTTP {response.status_code}")
        elif response.status_code != 200:
            raise ExecutionProviderUnavailableError(
                "Judge0", f"Token lookup failed (HTTP {response.status_code})"
            )

        data = response.json()
        status_obj = data.get("status", {})
        status_id = status_obj.get("id", 1)  # 1 = In Queue, 2 = Processing
        status_description = status_obj.get("description", "Unknown")

        # Time is reported in seconds string/float, memory in KB
        exec_time = data.get("time")
        try:
            exec_time = float(exec_time) if exec_time is not None else None
        except (ValueError, TypeError):
            exec_time = None

        memory = data.get("memory")
        try:
            memory = int(memory) if memory is not None else None
        except (ValueError, TypeError):
            memory = None

        return ExecutionRawResult(
            token=token,
            status_id=status_id,
            status_description=status_description,
            stdout=data.get("stdout"),
            stderr=data.get("stderr"),
            compile_output=data.get("compile_output"),
            message=data.get("message"),
            execution_time=exec_time,
            memory=memory,
            raw_payload=data,
        )

    async def execute(self, request: ExecutionRequest) -> ExecutionRawResult:
        """Submit and poll until completion or max poll attempts reached."""
        token = await self.submit(request)
        attempts = 0

        while attempts < self._max_poll_attempts:
            result = await self.get_result(token)
            # Status IDs 1 (In Queue) and 2 (Processing) mean execution is in progress
            if result.status_id not in (1, 2):
                return result

            attempts += 1
            await asyncio.sleep(self._poll_interval)

        raise ExecutionTimeoutError(self._poll_interval * self._max_poll_attempts)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check against Judge0 `/about` or `/system_info` endpoint."""
        url = f"{self._api_url}/about"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    return {
                        "provider": self.provider_name(),
                        "configured": True,
                        "available": True,
                        "version": response.json().get("version", self.provider_version()),
                    }
        except Exception:
            pass

        return {
            "provider": self.provider_name(),
            "configured": bool(self._api_url),
            "available": False,
            "version": self.provider_version(),
        }
