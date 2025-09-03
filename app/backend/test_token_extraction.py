#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_logging.chat_logger import chat_logger

# Test data mock pentru thoughts
class MockThought:
    def __init__(self, title, props=None):
        self.title = title
        self.props = props or {}

class MockTokenUsage:
    def __init__(self, prompt_tokens=0, completion_tokens=0, reasoning_tokens=0):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.reasoning_tokens = reasoning_tokens

# Test cu date mock
mock_thoughts = [
    MockThought("ModelQueryPlanning", {
        "query_plan": [
            {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150
            }
        ]
    }),
    MockThought("ChatCompletion", {
        "token_usage": MockTokenUsage(
            prompt_tokens=200,
            completion_tokens=75,
            reasoning_tokens=25
        )
    })
]

print("=== Test Token Extraction ===")

# Test agentic token extraction
print("\n1. Testing agentic token extraction:")
agentic_tokens = chat_logger._extract_agentic_token_usage(mock_thoughts)
print(f"Agentic tokens: {agentic_tokens} (type: {type(agentic_tokens)})")

# Test prompt token extraction
print("\n2. Testing prompt token extraction:")
prompt_tokens = chat_logger._extract_prompt_token_usage(mock_thoughts)
print(f"Prompt tokens: {prompt_tokens}")

# Test serialization
print("\n3. Testing thoughts serialization:")
serialized = chat_logger._serialize_thoughts(mock_thoughts)
print(f"Serialized length: {len(serialized) if serialized else 0}")
print(f"First 200 chars: {serialized[:200] if serialized else 'None'}...")

print("\n=== Test Complete ===")
