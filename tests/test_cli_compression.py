#!/usr/bin/env python3
"""Test CLI with context compression."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_BASE"] = "http://192.168.1.33:8080/v1"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["MODEL_NAME"] = "test-model"
os.environ["MODEL_CONTEXT_LENGTH"] = "128000"

from cli import SimpleCLI
from state import SimpleSessionDB


class TestCLICompression(unittest.TestCase):
    """Test CLI context compression integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.db = SimpleSessionDB()
        self.cli = SimpleCLI(session_db=self.db, auto_session=False)

    def test_compressor_initialized(self):
        """Test that compressor is initialized."""
        self.assertIsNotNone(self.cli.compressor)

    def test_compress_on_large_context(self):
        """Test compression triggers on large context."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "x" * 150000},
            {"role": "assistant", "content": "y" * 150000},
        ]

        tokens = sum(len(m["content"]) // 4 for m in messages)
        result = self.cli.compressor.should_compress(tokens)
        self.assertTrue(result)

    def test_no_compress_on_small_context(self):
        """Test no compression on small context."""
        messages = [{"role": "user", "content": "short"}]
        tokens = sum(len(m["content"]) // 4 for m in messages)
        result = self.cli.compressor.should_compress(tokens)
        self.assertFalse(result)

    def test_compress_preserves_system(self):
        """Test compression preserves system message."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "x" * 150000},
            {"role": "assistant", "content": "y" * 150000},
        ]

        compressed = self.cli.compressor.compress(messages, 2500)
        has_system = any(m.get("role") == "system" for m in compressed)
        self.assertTrue(has_system)

    def tearDown(self):
        """Clean up."""
        self.db.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
