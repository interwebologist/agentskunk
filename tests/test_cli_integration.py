#!/usr/bin/env python3
"""Test CLI with context compression."""

import sys
import os
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_BASE"] = "http://192.168.1.33:8080/v1"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["MODEL_NAME"] = "test-model"
os.environ["MODEL_CONTEXT_LENGTH"] = "128000"

from cli import SimpleCLI, run_single_query
from state import SimpleSessionDB


class TestCLISingleQuery(unittest.TestCase):
    """Test CLI single query mode."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, "state.db")

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_query_mode(self):
        """Test running a single query via CLI."""
        session_db = SimpleSessionDB()
        session_db.db_path = session_db.db_path.parent / "test_state.db"

        try:
            response = run_single_query("Hello, how are you?", session_db)
            self.assertIsNotNone(response)
            self.assertGreater(len(response), 0)
        finally:
            session_db.close()


class TestCLICompressionIntegration(unittest.TestCase):
    """Test CLI context compression integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, "state.db")

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_compresses_on_large_context(self):
        """Test that CLI compresses when context is large."""
        session_db = SimpleSessionDB()
        session_db.db_path = session_db.db_path.parent / "test_state.db"

        try:
            cli = SimpleCLI(session_db=session_db, auto_session=False)

            # Create a session
            session_id = session_db.create_session("test")
            cli.current_session_id = session_id
            cli.agent_history = []

            # Add many messages to trigger compression
            for i in range(20):
                cli.agent_history.append(
                    {
                        "role": "user",
                        "content": f"Question {i}" * 1000,
                    }
                )
                cli.agent_history.append(
                    {
                        "role": "assistant",
                        "content": f"Answer {i}" * 1000,
                    }
                )

            # Verify compressor exists
            self.assertIsNotNone(cli.compressor)

            # Check if compression would trigger
            tokens = sum(len(m["content"]) // 4 for m in cli.agent_history)
            should_compress = cli.compressor.should_compress(tokens)

            # Should compress with large context
            self.assertTrue(should_compress)

        finally:
            session_db.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
