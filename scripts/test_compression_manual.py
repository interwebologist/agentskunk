#!/usr/bin/env python3
"""Test script to manually trigger context compression."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["OPENAI_API_BASE"] = "http://192.168.1.33:8080/v1"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["MODEL_NAME"] = "test-model"
os.environ["MODEL_CONTEXT_LENGTH"] = "128000"

from agent.context_compressor import ContextCompressor
from agent.model_metadata import estimate_messages_tokens_rough


def test_compression_trigger():
    """Test that compression triggers at 50% threshold."""
    compressor = ContextCompressor(
        model="test-model",
        threshold_percent=0.50,
        quiet_mode=False,
    )

    print(f"Context length: {compressor.context_length}")
    print(f"Threshold tokens: {compressor.threshold_tokens}")
    print(f"Tail token budget: {compressor.tail_token_budget}")
    print()

    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
    ]

    for i in range(20):
        messages.append(
            {
                "role": "user",
                "content": f"Question {i}: Explain the concept of {i * 5000} lines of code. "
                * 5000,
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": f"Answer {i}: Here is a detailed explanation of {i * 5000} lines of code. "
                * 5000,
            }
        )

    initial_tokens = estimate_messages_tokens_rough(messages)
    print(f"Initial tokens: {initial_tokens}")
    print(f"Initial messages: {len(messages)}")
    print()

    should_compress = compressor.should_compress(initial_tokens)
    print(f"Should compress: {should_compress}")
    print()

    if should_compress:
        print("Testing compression...")
        compressed = compressor.compress(messages, initial_tokens)
        final_tokens = estimate_messages_tokens_rough(compressed)
        print(f"Final tokens: {final_tokens}")
        print(f"Final messages: {len(compressed)}")
        print(f"Tokens saved: {initial_tokens - final_tokens}")
        print(f"Percentage saved: {(1 - final_tokens / initial_tokens) * 100:.1f}%")
        print()

        print("First compressed message:")
        print(compressed[0])
        print()

        for i, msg in enumerate(compressed[:5]):
            print(f"Message {i}: {msg.get('role', 'unknown')} - {len(str(msg))} chars")
    else:
        print("Compression not triggered")


if __name__ == "__main__":
    test_compression_trigger()
