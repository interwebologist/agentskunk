"""Simplified context compression for MVP.

4-phase algorithm:
1. Remove old tool results from middle
2. Protect head (system + first 3) + tail (~20K)
3. Summarize middle with LLM
4. Merge: [HEAD] + [SUMMARY] + [TAIL]
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from agent.auxiliary_client import call_llm
from agent.model_metadata import (
    CHARS_PER_TOKEN,
    get_model_context_length,
    estimate_messages_tokens_rough,
)

logger = logging.getLogger(__name__)

_SUMMARY_PREFIX = (
    "[CONTEXT COMPACTION] Earlier turns summarized below. "
    "Your current task is in '## Active Task'. "
    "Respond ONLY to latest user message after this summary."
)

_SUMMARY_RATIO = 0.20
_SUMMARY_TOKENS_CEILING = 12_000
_PRUNED_TOOL_PLACEHOLDER = "[Old tool output cleared]"

_CONTENT_TAIL = 1500
_TOOL_ARGS_MAX = 1500
_TOOL_ARGS_HEAD = 1200


def _content_length_for_budget(raw_content: Any) -> int:
    """Return effective char-length for token budgeting."""
    if isinstance(raw_content, str):
        return len(raw_content)
    if not isinstance(raw_content, list):
        return len(str(raw_content or ""))
    total = 0
    for p in raw_content:
        if isinstance(p, str):
            total += len(p)
        elif isinstance(p, dict):
            ptype = p.get("type")
            if ptype in {"image_url", "input_image", "image"}:
                total += 1600 * CHARS_PER_TOKEN
            else:
                total += len(p.get("text", "") or "")
    return total


def _content_text_for_contains(content: Any) -> str:
    """Return best-effort text view of content for substring checks."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part)
    return str(content)


def _append_text_to_content(content: Any, text: str, *, prepend: bool = False) -> Any:
    """Append or prepend plain text to message content safely."""
    if content is None:
        return text
    if isinstance(content, str):
        return text + content if prepend else content + text
    if isinstance(content, list):
        text_block = {"type": "text", "text": text}
        return [text_block, *content] if prepend else [*content, text_block]
    rendered = str(content)
    return text + rendered if prepend else rendered + text


def _summarize_tool_result(tool_name: str, tool_args: str, tool_content: str) -> str:
    """Generate a 1-line summary of a tool result."""
    content_len = len(tool_content)
    args_preview = tool_args[:50] + "..." if len(tool_args) > 50 else tool_args
    if "exit" in tool_content.lower() or tool_name == "run_bash":
        exit_match = re.search(r"exit\s+(?:code\s+)?(\d+)", tool_content, re.IGNORECASE)
        exit_code = exit_match.group(1) if exit_match else "unknown"
        return f"[{tool_name}] ran `{args_preview}` -> exit {exit_code}, {content_len} chars"
    elif tool_name == "read_file":
        return f"[{tool_name}] read file `{args_preview}` ({content_len} chars)"
    return f"[{tool_name}] executed ({content_len} chars)"


def _truncate_tool_call_args_json(args: str, head_chars: int = 200) -> str:
    """Shrink long string values in tool args JSON."""
    try:
        parsed = json.loads(args)
    except json.JSONDecodeError:
        return args[:head_chars] + "...[truncated]"

    def shrink(obj: Any) -> Any:
        if isinstance(obj, str):
            return obj[:head_chars] + "...[truncated]" if len(obj) > head_chars else obj
        elif isinstance(obj, dict):
            return {k: shrink(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [shrink(item) for item in obj]
        return obj

    return json.dumps(shrink(parsed))


def _strip_image_parts_from_parts(parts: Any) -> Optional[List]:
    """Strip image parts from content parts list."""
    if not isinstance(parts, list):
        return None
    had_image = False
    out = []
    for part in parts:
        if not isinstance(part, dict):
            out.append(part)
            continue
        ptype = part.get("type")
        if ptype in {"image", "image_url", "input_image"}:
            had_image = True
            out.append({"type": "text", "text": "[image removed]"})
        else:
            out.append(part)
    return out if had_image else None


class ContextCompressor:
    """Simplified context compression for MVP."""

    def __init__(
        self,
        model: str,
        threshold_percent: float = 0.50,
        protect_first_n: int = 3,
        protect_last_n: int = 20,
        summary_target_ratio: float = 0.20,
        quiet_mode: bool = False,
        config_context_length: int | None = None,
    ):
        self.model = model
        self.context_length = config_context_length or get_model_context_length(model)
        self.threshold_percent = threshold_percent
        self.threshold_tokens = int(self.context_length * threshold_percent)
        self.protect_first_n = protect_first_n
        self.protect_last_n = protect_last_n
        self.summary_target_ratio = summary_target_ratio
        self.quiet_mode = quiet_mode

        self.tail_token_budget = int(self.threshold_tokens * summary_target_ratio)
        self.max_summary_tokens = min(
            self.context_length * 0.05, _SUMMARY_TOKENS_CEILING
        )

    def should_compress(self, prompt_tokens: int | None = None) -> bool:
        """Check if context exceeds threshold."""
        if prompt_tokens is None:
            return False
        return prompt_tokens >= self.threshold_tokens

    def _prune_old_tool_results(
        self,
        messages: List[Dict[str, Any]],
        protect_tail_count: int,
        protect_tail_tokens: int | None = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Remove old tool results from middle section."""
        if not messages:
            return messages, 0

        messages = [dict(m) for m in messages]
        total_chars_saved = 0

        if protect_tail_tokens is not None:
            backward_tokens = 0
            for i in range(len(messages) - 1, -1, -1):
                backward_tokens += _content_length_for_budget(
                    messages[i].get("content", "")
                )
                if backward_tokens > protect_tail_tokens:
                    protect_tail_count = len(messages) - i
                    break

        protected_start = max(0, len(messages) - protect_tail_count)

        for i, msg in enumerate(messages):
            if msg.get("role") == "tool" and i < protected_start:
                if isinstance(msg.get("content"), str) and len(msg["content"]) > 200:
                    prev_role_idx = i - 1
                    while (
                        prev_role_idx >= 0
                        and messages[prev_role_idx].get("role") != "assistant"
                    ):
                        prev_role_idx -= 1

                    tool_name = "unknown"
                    tool_args = ""
                    if prev_role_idx >= 0:
                        for tc in messages[prev_role_idx].get("tool_calls", []):
                            if tc.get("id") == msg.get("tool_call_id"):
                                tool_name = tc.get("function", {}).get(
                                    "name", "unknown"
                                )
                                tool_args = tc.get("function", {}).get("arguments", "")
                                break

                    summary = _summarize_tool_result(
                        tool_name, tool_args, msg["content"]
                    )
                    messages[i]["content"] = summary
                    total_chars_saved += len(msg["content"]) - len(summary)

        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "assistant" and messages[i].get("tool_calls"):
                for tc in messages[i]["tool_calls"]:
                    args = tc.get("function", {}).get("arguments", "")
                    if isinstance(args, str) and len(args) > _TOOL_ARGS_MAX:
                        truncated = _truncate_tool_call_args_json(args, _TOOL_ARGS_HEAD)
                        tc["function"]["arguments"] = truncated
                        total_chars_saved += len(args) - len(truncated)

        return messages, total_chars_saved

    def _protect_head_size(self, messages: List[Dict[str, Any]]) -> int:
        """Return count of head messages to protect."""
        count = 0
        if messages and messages[0].get("role") == "system":
            count = 1

        non_system_count = 0
        for i in range(count, len(messages)):
            if (
                messages[i].get("role") != "system"
                and messages[i].get("role") != "tool"
            ):
                non_system_count += 1
                if non_system_count >= self.protect_first_n:
                    break

        return count + non_system_count

    def _find_tail_cut_by_tokens(
        self,
        messages: List[Dict[str, Any]],
        head_end: int,
        token_budget: int | None = None,
    ) -> int:
        """Walk backward from end, accumulating tokens until budget reached."""
        if token_budget is None:
            return max(head_end, len(messages) - self.protect_last_n)

        if len(messages) <= 3:
            return max(head_end, 0)

        tail_tokens = 0
        cut_idx = len(messages)

        for i in range(len(messages) - 1, -1, -1):
            if i <= head_end:
                cut_idx = head_end + 1
                break

            tail_tokens += _content_length_for_budget(messages[i].get("content", ""))

            if tail_tokens > token_budget:
                if tail_tokens <= token_budget * 1.5:
                    cut_idx = i
                else:
                    cut_idx = i + 1
                break

        cut_idx = max(cut_idx, head_end + 1)
        cut_idx = max(cut_idx, len(messages) - self.protect_last_n)
        cut_idx = max(cut_idx, 1)

        return cut_idx

    def _ensure_last_user_message_in_tail(
        self,
        messages: List[Dict[str, Any]],
        tail_start: int,
    ) -> int:
        """Ensure most recent user message is in protected tail."""
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                return min(i, tail_start)
        return tail_start

    def _generate_summary(
        self,
        turns_to_summarize: List[Dict[str, Any]],
        focus_topic: str | None = None,
    ) -> Optional[str]:
        """Generate a structured summary of conversation turns."""
        if not turns_to_summarize:
            return None

        recent_user_msg = None
        for msg in reversed(turns_to_summarize):
            if msg.get("role") == "user":
                recent_user_msg = msg.get("content", "")
                break

        preamble = (
            "You are a summarization agent creating a context checkpoint. "
            "Treat the conversation turns below as source material. "
            "Produce only the structured summary; do not add greeting or preamble. "
            "Write in the same language the user was using. "
            "NEVER include API keys, tokens, passwords — replace with [REDACTED]."
        )

        summary_template = """## Active Task
[Copy user's most recent request verbatim]

## Completed Actions
1. [Action 1]
2. [Action 2]

## In Progress
- [Current task]

## Relevant Files
- path/to/file: [brief description]

## Resolved Questions
- [Question] → [Answer]

## Pending Questions
- [Question]

## Active State
- [Current state: files, config, etc.]

## Critical Context
[Any specific values, error messages, configuration details]
"""

        prompt_parts = [preamble]
        if recent_user_msg:
            prompt_parts.append(f"\nMost recent user request:\n{recent_user_msg}")
        prompt_parts.append("\n\nConversation turns to summarize:")

        for msg in turns_to_summarize:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    p.get("text", "") if isinstance(p, dict) else str(p)
                    for p in content
                )
            prompt_parts.append(f"\n--- {role.upper()} ---\n{content[:10000]}")

        full_prompt = "\n".join(prompt_parts) + "\n\n" + summary_template

        try:
            response = call_llm(
                [{"role": "user", "content": full_prompt}],
                max_tokens=self.max_summary_tokens,
            )
            if response and len(response.strip()) > 100:
                return response.strip()
            return None
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return None

    def _sanitize_tool_pairs(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Fix orphaned tool_call / tool_result pairs."""
        messages = [dict(m) for m in messages]

        call_ids = set()
        for msg in messages:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls", []):
                    call_ids.add(tc.get("id"))

        results_to_remove = []
        for i, msg in enumerate(messages):
            if msg.get("role") == "tool":
                tid = msg.get("tool_call_id")
                if tid and tid not in call_ids:
                    results_to_remove.append(i)

        for i in reversed(results_to_remove):
            logger.warning(f"Removing orphaned tool result at index {i}")
            del messages[i]

        new_call_ids = set()
        for msg in messages:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls", []):
                    new_call_ids.add(tc.get("id"))

        for i, msg in enumerate(messages):
            if msg.get("role") == "tool":
                tid = msg.get("tool_call_id")
                if tid and tid not in new_call_ids:
                    messages[i]["content"] = (
                        "[Result from earlier conversation — see context summary]"
                    )

        return messages

    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int | None = None,
        focus_topic: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Main compression entry point."""
        if current_tokens is None:
            current_tokens = estimate_messages_tokens_rough(messages)

        if len(messages) < 4:
            logger.warning("Cannot compress: insufficient messages")
            return messages

        messages, _ = self._prune_old_tool_results(
            messages, self.protect_last_n, self.tail_token_budget
        )

        head_end = self._protect_head_size(messages)
        tail_start = self._find_tail_cut_by_tokens(
            messages, head_end, self.tail_token_budget
        )
        tail_start = self._ensure_last_user_message_in_tail(messages, tail_start)

        turns_to_summarize = messages[head_end:tail_start]

        summary = self._generate_summary(turns_to_summarize, focus_topic)

        if summary is None:
            summary = "[Context compression failed — see original turns for context]"

        compressed = (
            messages[:head_end]
            + [{"role": "user", "content": _SUMMARY_PREFIX + "\n\n" + summary}]
            + messages[tail_start:]
        )

        system_msg = None
        for msg in compressed:
            if msg.get("role") == "system":
                system_msg = msg
                break

        if system_msg:
            from agent.context_compressor import (
                _content_text_for_contains,
                _append_text_to_content,
            )

            existing = _content_text_for_contains(system_msg.get("content", ""))
            if _SUMMARY_PREFIX not in existing:
                system_msg["content"] = _append_text_to_content(
                    system_msg.get("content", ""),
                    f"\n\n{_SUMMARY_PREFIX}",
                )

        compressed = self._sanitize_tool_pairs(compressed)

        for msg in compressed:
            if msg.get("role") == "assistant":
                content = msg.get("content")
                if isinstance(content, list):
                    stripped = _strip_image_parts_from_parts(content)
                    if stripped is not None:
                        msg["content"] = stripped

        new_tokens = estimate_messages_tokens_rough(compressed)
        savings_pct = (
            (1 - new_tokens / current_tokens) * 100 if current_tokens > 0 else 0
        )

        if not self.quiet_mode:
            logger.info(
                f"Compression: {len(messages)} msgs/{current_tokens} tokens -> "
                f"{len(compressed)} msgs/{new_tokens} tokens "
                f"({savings_pct:.1f}% saved)"
            )

        return compressed
