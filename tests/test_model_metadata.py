"""Test token estimation and model metadata."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_BASE"] = "http://192.168.1.33:8080/v1"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["MODEL_NAME"] = "test-model"
os.environ["MODEL_CONTEXT_LENGTH"] = "128000"

from agent.model_metadata import (
    estimate_messages_tokens_rough,
    get_model_context_length,
    CHARS_PER_TOKEN,
    MINIMUM_CONTEXT_LENGTH,
)


class TestModelMetadata(unittest.TestCase):
    """Test model metadata functions."""

    def test_chars_per_token_constant(self):
        """Test CHARS_PER_TOKEN constant."""
        self.assertEqual(CHARS_PER_TOKEN, 4)

    def test_minimum_context_length(self):
        """Test MINIMUM_CONTEXT_LENGTH constant."""
        self.assertEqual(MINIMUM_CONTEXT_LENGTH, 8192)

    def test_estimate_tokens_basic(self):
        """Test basic token estimation."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        tokens = estimate_messages_tokens_rough(messages)
        self.assertEqual(tokens, 2)

    def test_estimate_tokens_with_long_content(self):
        """Test token estimation with long content."""
        messages = [
            {"role": "user", "content": "x" * 100},
        ]
        tokens = estimate_messages_tokens_rough(messages)
        self.assertEqual(tokens, 25)

    def test_estimate_tokens_multimodal(self):
        """Test token estimation with multimodal content."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello"},
                    {"type": "image_url", "image_url": {"url": "http://example.com"}},
                ],
            },
        ]
        tokens = estimate_messages_tokens_rough(messages)
        self.assertGreater(tokens, 1)

    def test_get_model_context_length_env(self):
        """Test context length from environment."""
        length = get_model_context_length("test-model")
        self.assertEqual(length, 128000)

    def test_estimate_tokens_empty(self):
        """Test token estimation with empty messages."""
        messages = []
        tokens = estimate_messages_tokens_rough(messages)
        self.assertEqual(tokens, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
