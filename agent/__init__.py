"""Context compression module."""

from .context_compressor import ContextCompressor
from .model_metadata import estimate_messages_tokens_rough, get_model_context_length
from .auxiliary_client import call_llm

__all__ = [
    "ContextCompressor",
    "estimate_messages_tokens_rough",
    "get_model_context_length",
    "call_llm",
]

# Import run from agent.py for backward compatibility
import os

_agent_module_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "agent.py"
)

_agent_globals = {}
with open(_agent_module_path) as f:
    exec(f.read(), _agent_globals)

run = _agent_globals.get("run", None)
CHAT_HISTORY = _agent_globals.get("CHAT_HISTORY", [])
guardrails = _agent_globals.get("guardrails", None)
