import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any

from ai_review.providers.base_provider import BaseAIProvider
from ai_review.services.prompt_builder import ReviewPromptContext, PromptBuilder
from ai_review.services.validator import ResponseValidator
from ai_review.services.score_calculator import ScoreCalculator
from ai_review.utils.retry_handler import RetryHandler, NonRetryableError
from ai_review.utils.logger import SanitizedLogger
from ai_review.config import gemini_config

class GeminiProvider(BaseAIProvider):
    """Production-ready Gemini AI Provider implementing BaseAIProvider."""

    def __init__(self, config=None):
        self.config = config or gemini_config
        self.retry_handler = RetryHandler(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)

    def provider_name(self) -> str:
        return "Google Gemini Provider"

    def provider_version(self) -> str:
        return "1.0.0"

    def _strip_markdown_json(self, raw_text: str) -> str:
        text = raw_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    def _call_gemini_api(self, prompt: str) -> str:
        if not self.config.api_key:
            raise NonRetryableError("GEMINI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model_name}:generateContent?key={self.config.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_output_tokens,
                "responseMimeType": "application/json"
            }
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"}, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.config.request_timeout) as resp:
                body = resp.read().decode("utf-8")
                res_json = json.loads(body)
                candidates = res_json.get("candidates", [])
                if not candidates:
                    raise RuntimeError("No candidates returned from Gemini API.")
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise RuntimeError("No text parts returned from Gemini candidate.")
                
                return parts[0].get("text", "")
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8") if err.fp else str(err)
            if err.code in [401, 403]:
                raise NonRetryableError(f"Authentication failure ({err.code}): {err_body}")
            raise RuntimeError(f"Gemini API returned status {err.code}: {err_body}")
        except Exception as exc:
            raise RuntimeError(f"Gemini API request failed: {exc}")

    def generate_review(self, context: ReviewPromptContext) -> Dict[str, Any]:
        start_time = time.time()
        prompt = PromptBuilder.build_prompt(context)

        def _attempt():
            raw_output = self._call_gemini_api(prompt)
            clean_json_str = self._strip_markdown_json(raw_output)
            data = json.loads(clean_json_str)
            ResponseValidator.validate(data)
            return data

        try:
            parsed_data = self.retry_handler.execute(_attempt)
            duration_ms = int((time.time() - start_time) * 1000)

            # Compute overall score deterministically on the backend
            overall_score = ScoreCalculator.calculate_overall_score(parsed_data)
            parsed_data["overall_score"] = overall_score
            parsed_data["performance_score"] = parsed_data.get("optimization_score", 80.0)

            SanitizedLogger.log_request(
                provider=self.provider_name(),
                model=self.config.model_name,
                prompt_version=context.prompt_version,
                status="SUCCESS",
                latency_ms=duration_ms,
            )

            # Assemble complete review output dictionary
            return {
                "review_status": "COMPLETED",
                "overall_score": overall_score,
                "correctness_score": parsed_data.get("correctness_score"),
                "algorithm_score": parsed_data.get("algorithm_score"),
                "time_complexity_score": parsed_data.get("time_complexity_score"),
                "space_complexity_score": parsed_data.get("space_complexity_score"),
                "readability_score": parsed_data.get("readability_score"),
                "maintainability_score": parsed_data.get("maintainability_score"),
                "best_practices_score": parsed_data.get("best_practices_score"),
                "security_score": parsed_data.get("security_score"),
                "performance_score": parsed_data.get("performance_score"),
                "edge_case_score": parsed_data.get("edge_case_score"),
                "confidence_score": parsed_data.get("confidence_score", 90.0),
                "recommendation": parsed_data.get("recommendation", "PASS"),
                "time_complexity": parsed_data.get("time_complexity", "O(N)"),
                "space_complexity": parsed_data.get("space_complexity", "O(1)"),
                "ai_summary": parsed_data.get("summary", ""),
                "strengths": parsed_data.get("strengths", []),
                "weaknesses": parsed_data.get("weaknesses", []),
                "recommendations": parsed_data.get("optimization_suggestions", []),
                "score_reasoning": parsed_data.get("score_reasoning", {}),
                "code_issue_snippets": parsed_data.get("code_issue_snippets", []),
                "optimized_alternatives": parsed_data.get("optimized_alternatives", []),
                "expected_improvements": parsed_data.get("expected_improvements", {}),
                "review_trace": parsed_data.get("review_trace", {}),
                "structured_findings": parsed_data.get("structured_findings", {}),
                "provider": self.provider_name(),
                "provider_version": self.provider_version(),
                "model_name": self.config.model_name,
                "review_duration_ms": duration_ms,
                "prompt_version": context.prompt_version,
                "temperature": self.config.temperature,
            }
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            SanitizedLogger.log_request(
                provider=self.provider_name(),
                model=self.config.model_name,
                prompt_version=context.prompt_version,
                status="FAILED",
                latency_ms=duration_ms,
                error=str(exc),
            )
            raise exc

    def health_check(self) -> Dict[str, Any]:
        """Verify API key configuration and connectivity status."""
        if not self.config.api_key:
            return {
                "available": False,
                "provider": self.provider_name(),
                "version": self.provider_version(),
                "model": self.config.model_name,
                "status": "UNCONFIGURED_MISSING_API_KEY",
            }
        try:
            # Test ping with minimal prompt
            test_prompt = "Return JSON: {\"status\": \"ok\"}"
            self._call_gemini_api(test_prompt)
            return {
                "available": True,
                "provider": self.provider_name(),
                "version": self.provider_version(),
                "model": self.config.model_name,
                "status": "HEALTHY",
            }
        except Exception as exc:
            return {
                "available": False,
                "provider": self.provider_name(),
                "version": self.provider_version(),
                "model": self.config.model_name,
                "status": f"UNHEALTHY: {str(exc)}",
            }
