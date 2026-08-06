import os
from pydantic import BaseModel

class GeminiConfig(BaseModel):
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    model_name: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    temperature: float = float(os.getenv("TEMPERATURE", "0.2"))
    max_output_tokens: int = int(os.getenv("MAX_OUTPUT_TOKENS", "4096"))
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))

gemini_config = GeminiConfig()
