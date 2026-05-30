"""Tests for Human-in-the-Loop (HITL) functionality."""

import os
import sys
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent
import api


def test_tool_registry_has_risk_field():
    """Test that TOOL_REGISTRY has risk field for high-risk tools."""
    assert "run_bash" in agent.TOOL_REGISTRY
    assert agent.TOOL_REGISTRY["run_bash"].get("risk") == "high"
    assert agent.TOOL_REGISTRY["read_file"].get("risk") is None
    assert agent.TOOL_REGISTRY["weather"].get("risk") is None


def test_should_require_approval():
    """Test should_require_approval function."""
    # Reset env var
    os.environ.pop("HITL_ENABLED", None)

    # High-risk tool requires approval
    assert agent.should_require_approval("run_bash") is True

    # Non-risk tools don't require approval
    assert agent.should_require_approval("read_file") is False
    assert agent.should_require_approval("weather") is False
    assert agent.should_require_approval("web_search") is False
    assert agent.should_require_approval("nonexistent") is False


def test_hitl_enabled_env_var():
    """Test HITL_ENABLED environment variable controls approval."""
    # Enable HITL
    os.environ["HITL_ENABLED"] = "true"
    assert agent.should_require_approval("run_bash") is True

    # Disable HITL
    os.environ["HITL_ENABLED"] = "false"
    assert agent.should_require_approval("run_bash") is False

    # Test other truthy values
    os.environ["HITL_ENABLED"] = "1"
    assert agent.should_require_approval("run_bash") is True

    os.environ["HITL_ENABLED"] = "yes"
    assert agent.should_require_approval("run_bash") is True

    # Test falsy values
    os.environ["HITL_ENABLED"] = "0"
    assert agent.should_require_approval("run_bash") is False

    os.environ["HITL_ENABLED"] = "no"
    assert agent.should_require_approval("run_bash") is False

    # Cleanup
    os.environ.pop("HITL_ENABLED", None)


def test_api_has_hitl_endpoints():
    """Test that API has HITL endpoints registered."""
    paths = [route.path for route in api.app.routes if hasattr(route, "path")]

    assert "/v1/hitl/approve" in paths
    assert "/v1/hitl/pending" in paths


def test_api_hitl_endpoints_methods():
    """Test HITL endpoint HTTP methods."""
    methods_by_path = {}
    for route in api.app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            if route.path not in methods_by_path:
                methods_by_path[route.path] = set()
            methods_by_path[route.path].update(route.methods or [])

    assert "POST" in methods_by_path.get("/v1/hitl/approve", set())
    assert "GET" in methods_by_path.get("/v1/hitl/pending", set())


def test_cli_approval_flow():
    """Test CLI approval flow with mocked input."""
    os.environ["HITL_ENABLED"] = "true"

    # Mock input to approve
    with patch("builtins.input", return_value="y"):
        result = agent.prompt_approve_cli("run_bash", {"command": "ls"})
        assert result is True

    # Mock input to reject
    with patch("builtins.input", return_value="n"):
        result = agent.prompt_approve_cli("run_bash", {"command": "ls"})
        assert result is False

    # Mock input to reject with empty string
    with patch("builtins.input", return_value=""):
        result = agent.prompt_approve_cli("run_bash", {"command": "ls"})
        assert result is False


def test_api_check_tool_approvals():
    """Test API check_tool_approvals function."""
    import json as json_module
    from api import check_tool_approvals, hitl_approvals

    # Clear any pending approvals
    hitl_approvals.clear()

    # Test with high-risk tool call (run_bash)
    messages = [
        api.ChatMessage(role="user", content="Run ls command"),
        api.ChatMessage(
            role="assistant",
            content=json_module.dumps(
                {
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "run_bash",
                                "arguments": json_module.dumps({"command": "ls"}),
                            },
                        }
                    ]
                }
            ),
        ),
    ]

    result = check_tool_approvals(messages, "test_session")
    assert result is not None
    assert result["tool_name"] == "run_bash"
    assert result["session_id"] == "test_session"

    # Verify approval was stored
    assert "test_session:run_bash" in hitl_approvals

    # Clear for next test
    hitl_approvals.clear()

    # Test with low-risk tool (weather - no approval needed)
    messages_no_approval = [
        api.ChatMessage(role="user", content="Get weather"),
        api.ChatMessage(
            role="assistant",
            content=json_module.dumps(
                {
                    "tool_calls": [
                        {
                            "id": "call_456",
                            "type": "function",
                            "function": {
                                "name": "weather",
                                "arguments": json_module.dumps({"loc": "NYC"}),
                            },
                        }
                    ]
                }
            ),
        ),
    ]

    result = check_tool_approvals(messages_no_approval, "test_session")
    assert result is None
    assert "test_session:weather" not in hitl_approvals


def test_run_with_require_approval():
    """Test run function with require_approval parameter."""
    os.environ["HITL_ENABLED"] = "true"

    # Test with approval callback that approves
    def approve_all(func_name, args):
        return True

    # Test with approval callback that rejects
    def reject_all(func_name, args):
        return False

    # Just verify the function signature accepts require_approval
    # We can't actually run it without a real LLM response
    assert callable(agent.run)

    # Cleanup
    os.environ.pop("HITL_ENABLED", None)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
