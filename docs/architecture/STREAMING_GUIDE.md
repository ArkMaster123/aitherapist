# Streaming Inference Endpoint Guide

## Overview

This guide shows you how to deploy and use a **streaming inference endpoint** for your fine-tuned therapist model on Modal.

## What is Streaming?

Instead of waiting for the entire response, tokens are sent as they're generated - like ChatGPT's typing effect!

## Quick Start

### 1. Deploy the Endpoint

```bash
modal deploy streaming_inference.py
```

After deployment, you'll get a URL like:
```
https://your-workspace--therapist-streaming.modal.run/stream_chat
```

### 2. Test with curl

```bash
curl -X POST https://your-workspace--therapist-streaming.modal.run/stream_chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I feel anxious", "max_tokens": 256}'
```

You'll see tokens streaming in real-time:
```
data: {"token": "I", "done": false}

data: {"token": " understand", "done": false}

data: {"token": " that", "done": false}
...
data: {"token": "", "done": true}
```

### 3. Test with Python

```python
import requests
import json

url = "https://your-workspace--therapist-streaming.modal.run/stream_chat"

response = requests.post(
    url,
    json={
        "message": "I've been feeling stressed about work",
        "max_tokens": 256,
        "temperature": 0.7
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        decoded = line.decode()
        if decoded.startswith("data: "):
            data = json.loads(decoded[6:])  # Remove "data: " prefix
            if not data.get("done"):
                print(data["token"], end="", flush=True)
            else:
                print("\n[Stream complete]")
```

### 4. Test with JavaScript/Frontend

```javascript
const url = "https://your-workspace--therapist-streaming.modal.run/stream_chat";

const response = await fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "I feel anxious",
    max_tokens: 256,
  }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split("\n");
  
  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const data = JSON.parse(line.slice(6));
      if (!data.done) {
        // Append token to UI
        document.getElementById("response").textContent += data.token;
      }
    }
  }
}
```

## API Reference

### POST /stream_chat

**Request Body:**
```json
{
  "message": "Your message here",
  "conversation_history": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ],
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.9
}
```

**Parameters:**
- `message` (required): The user's message
- `conversation_history` (optional): Previous conversation context
- `max_tokens` (optional, default: 512): Maximum tokens to generate
- `temperature` (optional, default: 0.7): Sampling temperature (0-1)
- `top_p` (optional, default: 0.9): Nucleus sampling parameter

**Response:**
- Content-Type: `text/event-stream` (Server-Sent Events)
- Format: Each line is `data: {"token": "...", "done": false}`
- Final line: `data: {"token": "", "done": true}`

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model": "qwen_therapist_lora"
}
```

## Features

✅ **Real-time streaming** - Tokens appear as they're generated  
✅ **Conversation history** - Maintain context across messages  
✅ **Configurable parameters** - Control temperature, max tokens, etc.  
✅ **Serverless** - Scales automatically, pay only for usage  
✅ **GPU-powered** - Fast inference on A10G GPUs  
✅ **Model caching** - Model stays loaded for 5 minutes (faster responses)

## Cost

- **A10G GPU**: ~$0.30/hour
- **Container idle time**: 5 minutes (free after that)
- **First request**: ~10-20 seconds (model loading)
- **Subsequent requests**: ~2-5 seconds (model already loaded)

## Troubleshooting

**"Model not found" error:**
- Make sure training completed: `modal volume ls training-data`
- Check model path: `/data/qwen_therapist_lora`

**Slow first response:**
- Normal! Model loads on first request (~10-20 seconds)
- Subsequent requests are much faster

**Streaming not working:**
- Make sure you're using `stream=True` in requests
- Check that you're parsing SSE format correctly (`data: {...}`)

**Connection timeout:**
- Increase `max_tokens` if responses are very long
- Check Modal dashboard for errors: https://modal.com/apps

## Next Steps

1. **Integrate into your app** - Use the streaming endpoint in your frontend
2. **Add authentication** - Secure your endpoint with API keys
3. **Monitor usage** - Check Modal dashboard for costs and metrics
4. **Scale up** - Use H100 for faster inference if needed

## Example Integration

See `test_streaming_client.py` for a complete Python client example.

