#!/usr/bin/env python3
"""
Test function calling with your fine-tuned therapist model
"""
import os
import sys
from openai import OpenAI

# Get server URL
SERVER_URL = os.getenv("VLLM_SERVER_URL", "https://whataidea--vllm-therapist-serve.modal.run")

if not SERVER_URL:
    print("❌ Error: Set VLLM_SERVER_URL environment variable")
    sys.exit(1)

print(f"Testing function calling with: {SERVER_URL}")
print("="*70)

client = OpenAI(
    base_url=f"{SERVER_URL}/v1",
    api_key="not-needed"
)

# Define some example tools/functions
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_appointment",
            "description": "Schedule a therapy appointment",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time in HH:MM format"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Duration in minutes (30, 45, or 60)"
                    }
                },
                "required": ["date", "time"]
            }
        }
    }
]

# Test 1: Simple function call
print("\n1. Testing function calling with weather tool...")
print("   User: 'What's the weather in San Francisco?'\n")

try:
    response = client.chat.completions.create(
        model="qwen-therapist",
        messages=[
            {"role": "user", "content": "What's the weather in San Francisco?"}
        ],
        tools=tools,
        tool_choice="auto",  # Let model decide
        max_tokens=512,
    )
    
    message = response.choices[0].message
    print(f"✅ Response: {message.content}")
    
    if message.tool_calls:
        print(f"\n🔧 Function calls detected: {len(message.tool_calls)}")
        for tool_call in message.tool_calls:
            print(f"   - Function: {tool_call.function.name}")
            print(f"     Arguments: {tool_call.function.arguments}")
    else:
        print("\n⚠️  No function calls made (model might have answered directly)")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Therapy-specific function call
print("\n" + "="*70)
print("2. Testing function calling with appointment scheduling...")
print("   User: 'I'd like to schedule a therapy session for next Monday at 2pm'\n")

try:
    response = client.chat.completions.create(
        model="qwen-therapist",
        messages=[
            {"role": "user", "content": "I'd like to schedule a therapy session for next Monday at 2pm"}
        ],
        tools=tools,
        tool_choice="auto",
        max_tokens=512,
    )
    
    message = response.choices[0].message
    print(f"✅ Response: {message.content}")
    
    if message.tool_calls:
        print(f"\n🔧 Function calls detected: {len(message.tool_calls)}")
        for tool_call in message.tool_calls:
            print(f"   - Function: {tool_call.function.name}")
            print(f"     Arguments: {tool_call.function.arguments}")
    else:
        print("\n⚠️  No function calls made")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check if function calling is supported
print("\n" + "="*70)
print("3. Checking function calling support...")
print("   (Testing if the model can understand tool definitions)\n")

try:
    # Simple test with a clear function call scenario
    response = client.chat.completions.create(
        model="qwen-therapist",
        messages=[
            {"role": "user", "content": "Can you check the weather for me in New York?"}
        ],
        tools=tools,
        tool_choice="auto",
        max_tokens=200,
    )
    
    message = response.choices[0].message
    
    if message.tool_calls:
        print("✅ Function calling is WORKING! 🎉")
        print(f"   Model made {len(message.tool_calls)} function call(s)")
    elif message.content and "weather" in message.content.lower():
        print("⚠️  Model responded with text instead of calling function")
        print("   This might mean:")
        print("   - Function calling needs to be enabled in vLLM")
        print("   - Or the model needs more explicit prompting")
    else:
        print("⚠️  Unexpected response format")
        print(f"   Content: {message.content}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 This might mean:")
    print("   1. Function calling is not enabled in vLLM server")
    print("   2. Try deploying vllm_server_with_tools.py instead")
    print("   3. Or check vLLM server logs for errors")

print("\n" + "="*70)
print("✅ Function calling test complete!")
print("="*70)
print("\n💡 To enable function calling:")
print("   1. Deploy: modal deploy vllm_server_with_tools.py")
print("   2. Update VLLM_SERVER_URL to the new server URL")
print("   3. Run this test again")

