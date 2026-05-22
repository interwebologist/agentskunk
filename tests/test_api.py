#!/usr/bin/env python3
"""Test API endpoint for React agent tools."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test the API endpoint with tool usage."""
    print("Testing React Agent API")
    print("=" * 50)
    
    # Test 1: List tools
    print("\n1. Testing /v1/tools endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/v1/tools")
        tools = resp.json()
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['function']['name']}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: Test read_file via API
    print("\n2. Testing read_file via API...")
    try:
        resp = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant with access to tools."},
                    {"role": "user", "content": "Read the AGENTS.md file and tell me what it contains."}
                ],
                "temperature": 0.7
            }
        )
        result = resp.json()
        print(f"   Response: {result['choices'][0]['message']['content'][:300]}...")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Test weather via API
    print("\n3. Testing weather via API...")
    try:
        resp = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant with access to tools."},
                    {"role": "user", "content": "What's the weather in New York?"}
                ],
                "temperature": 0.7
            }
        )
        result = resp.json()
        print(f"   Response: {result['choices'][0]['message']['content'][:300]}...")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 4: Test web_search via API
    print("\n4. Testing web_search via API...")
    try:
        resp = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant with access to tools."},
                    {"role": "user", "content": "Search the web for 'python programming'"}
                ],
                "temperature": 0.7
            }
        )
        result = resp.json()
        print(f"   Response: {result['choices'][0]['message']['content'][:300]}...")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 5: Test web_fetch via API
    print("\n5. Testing web_fetch via API...")
    try:
        resp = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant with access to tools."},
                    {"role": "user", "content": "Fetch https://example.com and tell me what it contains."}
                ],
                "temperature": 0.7
            }
        )
        result = resp.json()
        print(f"   Response: {result['choices'][0]['message']['content'][:300]}...")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("API testing complete!")

if __name__ == "__main__":
    time.sleep(1)
    test_api()
