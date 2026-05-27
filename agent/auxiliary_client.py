"""Auxiliary LLM client for compression tasks."""

import logging
import os
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url=os.getenv("OPENAI_API_BASE", "http://192.168.1.33:8080/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
)


def call_llm(
    messages: list[dict[str, Any]],
    model: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """Call LLM and return response content.

    Args:
        messages: List of message dicts
        model: Model name (uses default if None)
        max_tokens: Maximum tokens to generate

    Returns:
        LLM response content
    """
    model_name = model or os.getenv("MODEL_NAME", "default-model")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


def is_connection_error(error: Exception) -> bool:
    """Check if error is a connection-related error."""
    import socket

    return isinstance(error, (socket.error, ConnectionError, TimeoutError))
