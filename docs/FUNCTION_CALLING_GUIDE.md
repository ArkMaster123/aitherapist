# Function Calling Guide for Your Fine-Tuned Model

## Can Your Model Do Function Calling? 🤔

**Short answer: YES!** 🎉

Qwen2.5-7B-Instruct natively supports function calling, and since your fine-tuning preserved the base model's architecture, function calling should still work!

## What is Function Calling?

Function calling (also called "tool use") allows your model to:
- Understand when to call external functions/tools
- Generate structured function calls with parameters
- Integrate with APIs, databases, calculators, etc.

**Example:**
```
User: "What's the weather in San Francisco?"
Model: [Calls get_weather(location="San Francisco")]
```

## Enable Function Calling

### Option 1: Update Your Existing vLLM Server

Edit `vllm_server.py` and add these flags to the `cmd` list:

```python
cmd = [
    "vllm",
    "serve",
    # ... existing flags ...
    "--enable-auto-tool-choice",  # Enable function calling
    "--tool-call-parser", "hermes",  # Qwen uses Hermes format
]
```

### Option 2: Use the New Server (Recommended)

I've created `vllm_server_with_tools.py` with function calling already enabled:

```bash
# Deploy the new server
modal deploy vllm_server_with_tools.py

# Get the new URL and update your environment
export VLLM_SERVER_URL=https://your-new-server-url.modal.run
```

## Testing Function Calling

Run the test script:

```bash
export VLLM_SERVER_URL=https://your-server-url.modal.run
python3 test_function_calling.py
```

This will test:
1. ✅ Basic function calling (weather example)
2. ✅ Therapy-specific functions (appointment scheduling)
3. ✅ Function calling support detection

## Using Function Calling in Your Code

### Python Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-server-url/v1",
    api_key="not-needed"
)

# Define your tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

# Make a request with tools
response = client.chat.completions.create(
    model="qwen-therapist",
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    tools=tools,
    tool_choice="auto",  # Let model decide
)

message = response.choices[0].message

# Check if model wants to call a function
if message.tool_calls:
    for tool_call in message.tool_calls:
        print(f"Function: {tool_call.function.name}")
        print(f"Arguments: {tool_call.function.arguments}")
        
        # Execute the function
        if tool_call.function.name == "get_weather":
            # Your function implementation here
            result = get_weather(location="NYC")
            
            # Send result back to model
            response = client.chat.completions.create(
                model="qwen-therapist",
                messages=[
                    {"role": "user", "content": "What's the weather in NYC?"},
                    message,  # Include the tool call
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    }
                ],
                tools=tools,
            )
```

## Therapy-Specific Function Examples

Here are some useful functions for a therapist chatbot:

### 1. Appointment Scheduling
```python
{
    "type": "function",
    "function": {
        "name": "schedule_appointment",
        "description": "Schedule a therapy appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "time": {"type": "string", "description": "HH:MM"},
                "duration": {"type": "integer", "description": "Minutes (30/45/60)"}
            },
            "required": ["date", "time"]
        }
    }
}
```

### 2. Mood Tracking
```python
{
    "type": "function",
    "function": {
        "name": "log_mood",
        "description": "Log the user's current mood",
        "parameters": {
            "type": "object",
            "properties": {
                "mood": {"type": "string", "enum": ["happy", "sad", "anxious", "calm", "angry"]},
                "intensity": {"type": "integer", "minimum": 1, "maximum": 10},
                "notes": {"type": "string"}
            },
            "required": ["mood", "intensity"]
        }
    }
}
```

### 3. Resource Lookup
```python
{
    "type": "function",
    "function": {
        "name": "find_resources",
        "description": "Find mental health resources in a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "type": {"type": "string", "enum": ["therapist", "support_group", "crisis_hotline"]}
            },
            "required": ["location"]
        }
    }
}
```

## Important Notes

1. **Fine-tuning Impact**: Your model was fine-tuned on therapist conversations, which might affect function calling behavior. Test it!

2. **vLLM Support**: Make sure you're using vLLM 0.11.2+ with `--enable-auto-tool-choice`

3. **Tool Choice Options**:
   - `"auto"` - Let model decide
   - `"required"` - Force model to use a tool
   - `"none"` - Disable tools
   - `{"type": "function", "function": {"name": "specific_tool"}}` - Force specific tool

4. **Testing**: Always test function calling after fine-tuning to ensure it still works!

## Troubleshooting

**Problem**: Model doesn't call functions
- ✅ Check vLLM server has `--enable-auto-tool-choice`
- ✅ Verify tool definitions are correct
- ✅ Try `tool_choice="required"` to force function calls
- ✅ Check server logs for errors

**Problem**: Function calls are malformed
- ✅ Check tool parameter schemas match JSON Schema spec
- ✅ Verify `--tool-call-parser hermes` is set (for Qwen)

**Problem**: Model ignores tools
- ✅ Make tool descriptions very clear
- ✅ Use examples in tool descriptions
- ✅ Try more explicit user prompts

## Next Steps

1. ✅ Deploy `vllm_server_with_tools.py`
2. ✅ Run `test_function_calling.py`
3. ✅ Add your own custom functions
4. ✅ Integrate with your therapy app!

---

**Your fine-tuned model CAN do function calling!** 🚀

