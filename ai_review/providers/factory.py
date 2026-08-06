import os
from ai_review.providers.base_provider import BaseAIProvider
from ai_review.providers.gemini_provider import GeminiProvider
from ai_review.providers.mock_provider import MockAIProvider
from ai_review.config import gemini_config

_provider_instance: BaseAIProvider = None

def get_ai_provider() -> BaseAIProvider:
    """Dependency Injection factory for AI Review providers."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    use_mock = os.getenv("USE_MOCK_PROVIDER", "false").lower() in ("true", "1")
    if use_mock or not gemini_config.api_key:
        _provider_instance = MockAIProvider()
    else:
        _provider_instance = GeminiProvider()
    return _provider_instance

def set_ai_provider(provider: BaseAIProvider) -> None:
    """Override AI provider instance for testing or alternative configurations."""
    global _provider_instance
    _provider_instance = provider
