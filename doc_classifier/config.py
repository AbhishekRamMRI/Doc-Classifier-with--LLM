"""Environment/config loading. No CLI dependencies."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")


def require_api_key() -> str:
    """Return the OpenAI API key or raise a clear error if it's missing."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your environment or a .env file."
        )
    return OPENAI_API_KEY
