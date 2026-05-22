#!/usr/bin/env python3
"""Unit tests for React agent tools."""
import sys
import unittest
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up test environment
os.environ["OPENAI_API_BASE"] = "http://192.168.1.33:8080/v1"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["MODEL_NAME"] = "test-model"

from tools.registry import registry, discover_builtin_tools
discover_builtin_tools()


class TestTools(unittest.TestCase):
    """Test all registered tools."""
    
    def setUp(self):
        """Reset registry before each test."""
        self.tools_tested = []
    
    def test_read_file(self):
        """Test read_file tool with existing file."""
        result = registry.dispatch("read_file", {"path": "AGENTS.md"})
        data = json.loads(result)
        self.assertIn("content", data)
        self.assertIn("path", data)
    
    def test_read_file_not_found(self):
        """Test read_file tool with non-existent file."""
        result = registry.dispatch("read_file", {"path": "/nonexistent/file.txt"})
        data = json.loads(result)
        self.assertIn("error", data)
    
    @patch("tools.weather_tool.requests.get")
    def test_weather_success(self, mock_get):
        """Test weather tool with mocked response."""
        mock_geo = MagicMock()
        mock_geo.json.return_value = {
            "results": [{"name": "New York", "latitude": 40.7128, "longitude": -74.0060}]
        }
        mock_weather = MagicMock()
        mock_weather.json.return_value = {
            "current_weather": {"temperature": 72.5},
            "hourly": {"temperature_2m": [70, 71, 72, 73, 74]}
        }
        mock_get.side_effect = [mock_geo, mock_weather]
        
        result = registry.dispatch("weather", {"loc": "New York"})
        data = json.loads(result)
        self.assertIn("location", data)
        self.assertIn("current_temp_f", data)
    
    @patch("tools.weather_tool.requests.get")
    def test_weather_not_found(self, mock_get):
        """Test weather tool with location not found."""
        mock_geo = MagicMock()
        mock_geo.json.return_value = {"results": []}
        mock_get.return_value = mock_geo
        
        result = registry.dispatch("weather", {"loc": "NonExistentCity12345"})
        data = json.loads(result)
        self.assertIn("error", data)
    
    @patch("ddgs.DDGS")
    def test_web_search_success(self, mock_ddgs):
        """Test web_search tool with mocked DDGS."""
        mock_ddgs.return_value.__enter__.return_value.text.return_value = [
            {"title": "Test Result", "body": "Test snippet", "href": "https://example.com"}
        ]
        
        result = registry.dispatch("web_search", {"query": "test query"})
        data = json.loads(result)
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 1)
    
    @patch("ddgs.DDGS")
    def test_web_search_no_results(self, mock_ddgs):
        """Test web_search tool with no results."""
        mock_ddgs.return_value.__enter__.return_value.text.return_value = []
        
        result = registry.dispatch("web_search", {"query": "nonexistentquery12345"})
        data = json.loads(result)
        self.assertIn("error", data)
    
    @patch("tools.google_search_tool.requests.request")
    def test_google_search_success(self, mock_request):
        """Test google_search tool with mocked response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "organic": [
                {"title": "Google Result", "link": "https://google.com", "snippet": "Test snippet"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        result = registry.dispatch("google_search", {"q": "test query"})
        data = json.loads(result)
        self.assertIn("results", data)
    
    @patch("tools.google_search_tool.requests.request")
    def test_google_search_no_results(self, mock_request):
        """Test google_search tool with no organic results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"organic": []}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        result = registry.dispatch("google_search", {"q": "test query"})
        data = json.loads(result)
        self.assertIn("error", data)
    
    @patch("tools.web_fetch_tool.requests.get")
    def test_web_fetch_success(self, mock_get):
        """Test web_fetch tool with mocked response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        mock_get.return_value = mock_response
        
        result = registry.dispatch("web_fetch", {"url": "https://example.com"})
        data = json.loads(result)
        self.assertIn("content", data)
        self.assertIn("Test", data["content"])
    
    @patch("tools.web_fetch_tool.requests.get")
    def test_web_fetch_github_raw(self, mock_get):
        """Test web_fetch tool with GitHub URL."""
        mock_raw = MagicMock()
        mock_raw.status_code = 200
        mock_raw.text = "# Test Repo\n\nSome code"
        mock_get.return_value = mock_raw
        
        result = registry.dispatch("web_fetch", {
            "url": "https://github.com/testuser/testrepo/blob/main/README.md"
        })
        data = json.loads(result)
        self.assertIn("content", data)
    
    def test_clear_topic(self):
        """Test clear_topic tool."""
        import agent
        agent.CHAT_HISTORY = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]
        
        result = registry.dispatch("clear_topic", {})
        data = json.loads(result)
        self.assertTrue(data["topic_cleared"])
        self.assertEqual(len(agent.CHAT_HISTORY), 1)
        self.assertEqual(agent.CHAT_HISTORY[0]["role"], "system")
    
    def test_clear_topic_with_new_topic(self):
        """Test clear_topic tool with new topic."""
        import agent
        agent.CHAT_HISTORY = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]
        
        result = registry.dispatch("clear_topic", {"new_topic": "Programming"})
        data = json.loads(result)
        self.assertTrue(data["topic_cleared"])
        self.assertEqual(data["new_topic"], "Programming")


class TestToolRegistry(unittest.TestCase):
    """Test the tool registry."""
    
    def test_get_all_tool_names(self):
        """Test that all expected tools are registered."""
        tool_names = registry.get_all_tool_names()
        expected = ["read_file", "weather", "web_search", "google_search", "web_fetch", "clear_topic"]
        for tool in expected:
            self.assertIn(tool, tool_names, f"Tool {tool} not registered")
    
    def test_get_tool_definitions(self):
        """Test getting tool definitions in OpenAI format."""
        tool_names = {"read_file", "weather"}
        definitions = registry.get_definitions(tool_names=tool_names)
        self.assertEqual(len(definitions), 2)
        for defn in definitions:
            self.assertIn("type", defn)
            self.assertEqual(defn["type"], "function")
            self.assertIn("function", defn)
            self.assertIn("name", defn["function"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
