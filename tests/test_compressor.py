#!/usr/bin/env python3
"""Test context compression functionality."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_BASE"] = "http://192.168.1.33:8080/v1"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["MODEL_NAME"] = "test-model"
os.environ["MODEL_CONTEXT_LENGTH"] = "128000"

from agent.context_compressor import ContextCompressor
from agent.model_metadata import (
    estimate_messages_tokens_rough,
    get_model_context_length,
)


class TestContextCompressor(unittest.TestCase):
    """Test context compression functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )

    def test_estimate_tokens_rough(self):
        """Test token estimation function."""
        messages = [
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        tokens = estimate_messages_tokens_rough(messages)
        self.assertGreater(tokens, 0)

    def test_get_model_context_length(self):
        """Test model context length retrieval."""
        length = get_model_context_length("test-model")
        self.assertEqual(length, 128000)

    def test_should_compress_below_threshold(self):
        """Test should_compress returns False below threshold."""
        messages = [{"role": "user", "content": "test"}]
        tokens = estimate_messages_tokens_rough(messages)
        result = self.compressor.should_compress(tokens)
        self.assertFalse(result)

    def test_should_compress_above_threshold(self):
        """Test should_compress returns True above threshold."""
        messages = [{"role": "user", "content": "x" * 300000}]
        tokens = estimate_messages_tokens_rough(messages)
        result = self.compressor.should_compress(tokens)
        self.assertTrue(result)

    def test_protect_head_size(self):
        """Test head message protection count."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
        ]
        head_end = self.compressor._protect_head_size(messages)
        self.assertGreaterEqual(head_end, 1)

    def test_prune_old_tool_results(self):
        """Test tool result pruning."""
        messages = [
            {"role": "user", "content": "Run tests"},
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call1",
                        "function": {
                            "name": "run_bash",
                            "arguments": '{"command": "npm test"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call1",
                "content": "exit code 0\n" + "output\n" * 50,
            },
        ]
        pruned, saved = self.compressor._prune_old_tool_results(messages, 1)
        self.assertGreaterEqual(len(pruned), 1)

    def test_sanitize_tool_pairs(self):
        """Test orphaned tool pair handling."""
        messages = [
            {"role": "user", "content": "Test"},
            {"role": "tool", "tool_call_id": "orphan", "content": "orphaned"},
        ]
        sanitized = self.compressor._sanitize_tool_pairs(messages)
        self.assertEqual(len(sanitized), 1)

    def test_compress_small_context(self):
        """Test compression with small context."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant response"},
            {"role": "user", "content": "Another user message"},
        ]
        tokens = sum(len(m["content"]) // 4 for m in messages)
        compressed = self.compressor.compress(messages, tokens)
        self.assertGreaterEqual(len(compressed), 1)


class TestContextCompressorIntegration(unittest.TestCase):
    """Integration tests for context compression."""

    def test_full_compression_cycle(self):
        """Test complete compression cycle with multiple messages."""
        compressor = ContextCompressor(
            model="test-model",
            threshold_percent=0.50,
            quiet_mode=True,
        )

        messages = [
            {"role": "system", "content": "You are a helpful coding assistant."},
        ]

        for i in range(15):
            messages.append(
                {
                    "role": "user",
                    "content": f"Question {i}: What is the meaning of life?",
                }
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": f"Answer {i}: Based on my analysis, the answer is 42.",
                }
            )

        initial_tokens = estimate_messages_tokens_rough(messages)
        compressed = compressor.compress(messages, initial_tokens)
        final_tokens = estimate_messages_tokens_rough(compressed)

        self.assertGreaterEqual(final_tokens, 0)
        self.assertIn("[CONTEXT COMPACTION", str(compressed))


if __name__ == "__main__":
    unittest.main(verbosity=2)
