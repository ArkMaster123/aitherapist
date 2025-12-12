#!/usr/bin/env python3
"""Quick test of vLLM server connection"""
import os
import sys
from openai import OpenAI

SERVER_URL = os.getenv("VLLM_SERVER_URL", "https://whataidea--vllm-therapist-serve.modal.run")

if not SERVER_URL:
    print("❌ Error: Set VLLM_SERVER_URL environment variable")
    sys.exit(1)

print(f"Testing connection to: {SERVER_URL}")
print("="*70)

client = OpenAI(
    base_url=f"{SERVER_URL}/v1",
    api_key="not-needed"
)

# Test 1: Non-streaming
print("\n1. Testing non-streaming request...")
try:
    response = client.chat.completions.create(
        model="qwen-therapist",
        messages=[{"role": "user", "content": "Say hello in one sentence"}],
        stream=False,
        max_tokens=50,
    )
    print(f"✅ Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Streaming
print("\n2. Testing streaming request...")
try:
    response = client.chat.completions.create(
        model="qwen-therapist",
        messages=[{"role": "user", "content": "Count to 3"}],
        stream=True,
        max_tokens=50,
    )
    print("✅ Streaming response: ", end="", flush=True)
    for chunk in response:
        if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                print(delta.content, end="", flush=True)
    print()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: With history
print("\n3. Testing with conversation history...")
try:
    messages = [
        {"role": "user", "content": "My name is Alice"},
        {"role": "assistant", "content": "Nice to meet you, Alice!"},
        {"role": "user", "content": "What's my name?"}
    ]
    response = client.chat.completions.create(
        model="qwen-therapist",
        messages=messages,
        stream=False,
        max_tokens=50,
    )
    print(f"✅ Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("✅ All tests complete!")

