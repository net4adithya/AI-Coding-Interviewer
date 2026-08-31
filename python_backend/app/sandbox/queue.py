"""Redis-backed execution job queue."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Dict, Optional

import redis

from app.sandbox.config import sandbox_settings
from app.sandbox.schemas import ExecutionResponse

logger = logging.getLogger(__name__)


class ExecutionQueue:
    def __init__(self) -> None:
        self._redis = redis.Redis(
            host=sandbox_settings.REDIS_HOST,
            port=sandbox_settings.REDIS_PORT,
            password=sandbox_settings.REDIS_PASSWORD or None,
            db=sandbox_settings.REDIS_DB,
            decode_responses=True,
        )

    def ping(self) -> bool:
        return bool(self._redis.ping())

    def _result_key(self, job_id: str) -> str:
        return f"{sandbox_settings.EXECUTION_RESULT_PREFIX}{job_id}"

    def _status_key(self, job_id: str) -> str:
        return f"{sandbox_settings.EXECUTION_RESULT_PREFIX}{job_id}:status"

    def enqueue(self, payload: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job = {"job_id": job_id, **payload}
        pipe = self._redis.pipeline()
        pipe.lpush(sandbox_settings.EXECUTION_QUEUE_KEY, json.dumps(job))
        pipe.set(self._status_key(job_id), "PENDING", ex=sandbox_settings.EXECUTION_RESULT_TTL_SEC)
        pipe.execute()
        logger.info("[SandboxQueue] Enqueued job %s lang=%s", job_id, payload.get("language"))
        return job_id

    def set_result(self, job_id: str, result: ExecutionResponse) -> None:
        data = result.model_dump()
        data["job_id"] = job_id
        pipe = self._redis.pipeline()
        pipe.set(self._result_key(job_id), json.dumps(data), ex=sandbox_settings.EXECUTION_RESULT_TTL_SEC)
        pipe.set(self._status_key(job_id), "COMPLETED", ex=sandbox_settings.EXECUTION_RESULT_TTL_SEC)
        pipe.execute()

    def get_result(self, job_id: str) -> Optional[ExecutionResponse]:
        raw = self._redis.get(self._result_key(job_id))
        if not raw:
            return None
        data = json.loads(raw)
        return ExecutionResponse(**data)

    def wait_for_result(self, job_id: str, timeout_sec: Optional[float] = None) -> Optional[ExecutionResponse]:
        deadline = time.time() + (timeout_sec or sandbox_settings.JOB_WAIT_TIMEOUT_SEC)
        while time.time() < deadline:
            result = self.get_result(job_id)
            if result is not None:
                return result
            time.sleep(0.15)
        return None

    def blocking_pop_job(self, timeout_sec: int = 5) -> Optional[Dict[str, Any]]:
        item = self._redis.brpop(sandbox_settings.EXECUTION_QUEUE_KEY, timeout=timeout_sec)
        if not item:
            return None
        _, raw = item
        return json.loads(raw)
