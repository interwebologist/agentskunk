"""Test auxiliary client."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_BASE"] = "http://192.168.1.33:8080/v1"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["MODEL_NAME"] = "test-model"
os.environ["MODEL_CONTEXT_LENGTH"] = "128000"


class TestAuxiliaryClient(unittest.TestCase):
    """Test auxiliary client functions."""

    def test_is_connection_error(self):
        """Test connection error detection."""
        from agent.auxiliary_client import is_connection_error

        self.assertTrue(is_connection_error(ConnectionError()))
        self.assertTrue(is_connection_error(OSError()))
        self.assertFalse(is_connection_error(ValueError()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
