"""
llm_fallback.py
---------------
• Primary:  OpenAI GPT (model passed by caller)
• Fallback: Groq AI  (llama-3.3-70b-versatile)

Fallback triggers only when OpenAI returns a 429 insufficient_quota error.
All other exceptions propagate normally.

DALL-E / image generation is NOT touched — this file is text/LLM only.
"""

import logging
import os
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: detect insufficient_quota regardless of SDK version
# ---------------------------------------------------------------------------

def _is_insufficient_quota(exc: Exception) -> bool:
    """Return True if exc is an OpenAI 429 insufficient_quota error.

    Checks multiple locations because exc.body structure varies across
    openai SDK versions (sometimes nested, sometimes flat, sometimes None).
    The string representation is the final guaranteed fallback — the SDK
    always embeds the error dict in str(exc).
    """
    # Method 1: structured body dict
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        # Standard shape: {"error": {"code": "insufficient_quota", "type": ...}}
        inner = body.get("error", {})
        if isinstance(inner, dict):
            if inner.get("code") == "insufficient_quota":
                return True
            if inner.get("type") == "insufficient_quota":
                return True
        # Flat shape: body IS the inner dict already
        if body.get("code") == "insufficient_quota":
            return True
        if body.get("type") == "insufficient_quota":
            return True

    # Method 2: string fallback — always works regardless of SDK version
    # str(exc) looks like: "Error code: 429 - {'error': {'code': 'insufficient_quota', ...}}"
    return "insufficient_quota" in str(exc)


# ---------------------------------------------------------------------------
# Helper: build Groq client (OpenAI-compatible endpoint)
# ---------------------------------------------------------------------------

def _build_groq_llm(temperature: float) -> ChatOpenAI:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file."
        )
    # Debug: confirm which key is being used (first 10 chars only)
    print(f"[llm_fallback] Using Groq key: {groq_api_key[:10]}...")
    # NOTE: ChatOpenAI uses openai_api_key / openai_api_base — NOT api_key / base_url.
    # Passing the wrong parameter name causes it to silently use OPENAI_API_KEY instead.
    return ChatOpenAI(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        openai_api_base="https://api.groq.com/openai/v1",
        openai_api_key=groq_api_key,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def invoke_with_fallback(
    messages: list[BaseMessage],
    *,
    openai_model: str = "gpt-4o",
    temperature: float = 0.7,
) -> Any:
    """
    Call OpenAI; if quota is exhausted (429 insufficient_quota), retry on Groq.

    Parameters
    ----------
    messages      : LangChain message list (SystemMessage, HumanMessage, …)
    openai_model  : OpenAI model to try first  (default: "gpt-4o")
    temperature   : Sampling temperature for both providers

    Returns
    -------
    AIMessage from whichever provider succeeded.
    """
    # max_retries=0 → the SDK raises immediately on 429 instead of
    # internally retrying up to 3 times (which caused the error to bubble
    # past this try/except before we could intercept it).
    primary_llm = ChatOpenAI(
        model=openai_model,
        temperature=temperature,
        max_retries=0,
    )

    try:
        logger.debug("[llm_fallback] Trying OpenAI model=%s", openai_model)
        return primary_llm.invoke(messages)

    except Exception as exc:
        # Broad catch so we never miss the error due to an import alias
        # or SDK version wrapping it in a different exception subclass.
        if _is_insufficient_quota(exc):
            # Use print() as well so it's visible regardless of log level.
            msg = (
                "⚠️  [llm_fallback] OpenAI quota exhausted (429 insufficient_quota). "
                "Switching to Groq llama-3.3-70b-versatile."
            )
            print(msg)
            logger.warning(msg)
            fallback_llm = _build_groq_llm(temperature)
            return fallback_llm.invoke(messages)

        # Any other error (auth failure, network error, etc.) — re-raise as-is.
        logger.error("[llm_fallback] Non-quota error from OpenAI: %s", exc)
        raise
