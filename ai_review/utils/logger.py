import logging
import re
from typing import Dict, Any

logger = logging.getLogger("ai_review.telemetry")

class SanitizedLogger:
    @staticmethod
    def _sanitize(message: str) -> str:
        # Mask API keys matching common patterns e.g. AIzaSy... or Bearer tokens
        sanitized = re.sub(r'(AIzaSy[A-Za-z0-9_-]{33})', '[REDACTED_API_KEY]', message)
        sanitized = re.sub(r'(key|api_key|secret)=["\']?[A-Za-z0-9_-]+["\']?', r'\1=[REDACTED]', sanitized, flags=re.IGNORECASE)
        return sanitized

    @classmethod
    def log_request(cls, provider: str, model: str, prompt_version: str, status: str, latency_ms: int, token_usage: Dict[str, Any] = None, error: str = None):
        log_data = f"Provider={provider} | Model={model} | PromptVer={prompt_version} | Status={status} | Latency={latency_ms}ms | Tokens={token_usage or {}}"
        if error:
            log_data += f" | Error={cls._sanitize(error)}"
        
        if status == "SUCCESS":
            logger.info(cls._sanitize(log_data))
        else:
            logger.error(cls._sanitize(log_data))
