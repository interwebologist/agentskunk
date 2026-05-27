"""Token estimation and model metadata utilities."""

from typing import Any

CHARS_PER_TOKEN = 4
MINIMUM_CONTEXT_LENGTH = 8192


def estimate_messages_tokens_rough(messages: list[dict[str, Any]]) -> int:
    """Estimate token count for messages using 4 chars/token rule.

    Args:
        messages: List of message dicts with 'content' field

    Returns:
        Estimated token count
    """
    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, str):
                    total_chars += len(part)
                elif isinstance(part, dict):
                    text = part.get("text", "")
                    if isinstance(text, str):
                        total_chars += len(text)
    return (total_chars + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


def get_model_context_length(model: str) -> int:
    """Get context length for a model.

    Args:
        model: Model name (e.g., "NVIDIA-Nemotron-3-Super-120B-A12B-UD-Q4_K_XL.gguf")

    Returns:
        Context window in tokens (default 128K for unknown models)
    """
    import os

    env_length = os.getenv("MODEL_CONTEXT_LENGTH")
    if env_length:
        try:
            return int(env_length)
        except ValueError:
            pass
    return 128000
