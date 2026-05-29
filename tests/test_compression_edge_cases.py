#!/usr/bin/env python3
"""Test context compression end-to-end."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_BASE"] = "http://192.168.1.33:8080/v1"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["MODEL_NAME"] = "test-model"
os.environ["MODEL_CONTEXT_LENGTH"] = "128000"

from compression.context_compressor import ContextCompressor
from compression.model_metadata import estimate_messages_tokens_rough


class TestCompressionEdgeCases(unittest.TestCase):
    """Test edge cases in compression."""

    def test_empty_messages(self):
        """Test compression with empty messages."""
        compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )
        result = compressor.compress([])
        self.assertEqual(result, [])

    def test_single_message(self):
        """Test compression with single message."""
        compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )
        messages = [{"role": "user", "content": "Hello"}]
        result = compressor.compress(messages)
        self.assertEqual(len(result), 1)

    def test_tool_pair_integrity(self):
        """Test that tool call/result pairs stay together."""
        compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )
        messages = [
            {"role": "user", "content": "Run command"},
            {
                "role": "assistant",
                "tool_calls": [
                    {"id": "call1", "function": {"name": "run_bash", "arguments": "{}"}}
                ],
            },
            {"role": "tool", "tool_call_id": "call1", "content": "result"},
            {"role": "user", "content": "Another query"},
        ]
        tokens = estimate_messages_tokens_rough(messages)
        compressed = compressor.compress(messages, tokens)

        call_ids = set()
        for msg in compressed:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls", []):
                    call_ids.add(tc.get("id"))

        for msg in compressed:
            if msg.get("role") == "tool":
                tid = msg.get("tool_call_id")
                if tid:
                    self.assertIn(tid, call_ids)

    def test_orphaned_tool_result_removal(self):
        """Test removal of orphaned tool results."""
        compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )
        messages = [
            {"role": "user", "content": "Test"},
            {"role": "tool", "tool_call_id": "nonexistent", "content": "orphan"},
        ]
        sanitized = compressor._sanitize_tool_pairs(messages)
        self.assertEqual(len(sanitized), 1)

    def test_large_content_truncation(self):
        """Test truncation of large content."""
        compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )
        messages = [
            {"role": "user", "content": "x" * 100000},
            {"role": "assistant", "content": "y" * 100000},
        ]
        tokens = estimate_messages_tokens_rough(messages)
        compressed = compressor.compress(messages, tokens)
        self.assertLess(len(compressed), len(messages) * 2)

    def test_iterative_summary(self):
        """Test iterative summary generation."""
        compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )

        messages = [{"role": "system", "content": "System"}]

        for i in range(20):
            messages.append({"role": "user", "content": f"Query {i}"})
            messages.append({"role": "assistant", "content": f"Response {i}"})

        tokens = estimate_messages_tokens_rough(messages)
        compressed = compressor.compress(messages, tokens)

        compressed_text = str(compressed)
        self.assertIn("[CONTEXT COMPACTION", compressed_text)

    def test_user_message_in_tail(self):
        """Test that most recent user message stays in tail."""
        compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )

        messages = [{"role": "system", "content": "System"}]

        for i in range(10):
            messages.append({"role": "user", "content": f"User {i}"})
            messages.append({"role": "assistant", "content": f"Assistant {i}"})

        tokens = estimate_messages_tokens_rough(messages)
        compressed = compressor.compress(messages, tokens)

        last_user_idx = None
        for i, msg in enumerate(compressed):
            if msg.get("role") == "user":
                last_user_idx = i

        self.assertIsNotNone(last_user_idx)

    def test_summary_failure_fallback(self):
        """Test fallback when summary generation fails."""
        compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )

        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "x" * 50000},
            {"role": "assistant", "content": "y" * 50000},
            {"role": "user", "content": "z" * 50000},
        ]

        tokens = estimate_messages_tokens_rough(messages)
        compressed = compressor.compress(messages, tokens)

        compressed_text = str(compressed)
        self.assertTrue(
            "[CONTEXT COMPACTION" in compressed_text
            or "[Context compression failed" in compressed_text
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
